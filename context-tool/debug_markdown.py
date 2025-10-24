"""Debug script to check markdown mode data loading"""

from pathlib import Path
from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer

# Initialize database
print("=" * 60)
print("Debug: Markdown Mode Data Loading")
print("=" * 60)

db = get_database(":memory:")
data_dir = Path("./data-md")

print(f"\nData directory: {data_dir}")
print(f"Exists: {data_dir.exists()}")

if data_dir.exists():
    print("\nLoading markdown data...")
    load_data(db.connection, data_dir, format='markdown')

    # Check what was loaded
    print("\n" + "-" * 60)
    print("DATABASE CONTENTS:")
    print("-" * 60)

    # Check abbreviations
    cursor = db.connection.execute("SELECT abbr, full FROM abbreviations")
    abbrs = cursor.fetchall()
    print(f"\nAbbreviations ({len(abbrs)}):")
    for row in abbrs:
        print(f"  - {row['abbr']} = {row['full']}")

    # Check contacts
    cursor = db.connection.execute("SELECT name, email FROM contacts")
    contacts = cursor.fetchall()
    print(f"\nContacts ({len(contacts)}):")
    for row in contacts:
        print(f"  - {row['name']} ({row['email'] or 'no email'})")

    print("\n" + "-" * 60)
    print("TESTING MATCHES:")
    print("-" * 60)

    # Create analyzer
    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    # Test LLM
    print("\n1. Testing 'llm':")
    result = analyzer.analyze("llm")
    if result.get('abbreviation'):
        print(f"   ✓ FOUND: {result['abbreviation']['abbr']} = {result['abbreviation']['full']}")
    else:
        print(f"   ✗ NOT FOUND")
        print(f"   Detected type: {result.get('detected_type')}")
        print(f"   Exact matches: {len(result.get('exact_matches', []))}")

    # Test Magnus
    print("\n2. Testing 'Magnus':")
    result = analyzer.analyze("Magnus")
    exact_matches = result.get('exact_matches', [])
    contact_matches = [m for m in exact_matches if m['type'] == 'contact']
    if contact_matches:
        print(f"   ✓ FOUND: {contact_matches[0]['data']['name']}")
    else:
        print(f"   ✗ NOT FOUND")
        print(f"   Detected type: {result.get('detected_type')}")
        print(f"   Exact matches: {len(exact_matches)}")
        if exact_matches:
            print(f"   Match types: {[m['type'] for m in exact_matches]}")

    # Test direct SQL queries
    print("\n" + "-" * 60)
    print("DIRECT SQL QUERIES:")
    print("-" * 60)

    print("\n3. Direct query for 'LLM':")
    cursor = db.connection.execute("""
        SELECT abbr, full FROM abbreviations
        WHERE UPPER(abbr) = UPPER('llm')
    """)
    row = cursor.fetchone()
    if row:
        print(f"   ✓ FOUND: {row['abbr']} = {row['full']}")
    else:
        print(f"   ✗ NOT FOUND")

    print("\n4. Direct query for 'Magnus':")
    cursor = db.connection.execute("""
        SELECT name FROM contacts
        WHERE LOWER(name) LIKE LOWER('%magnus%')
    """)
    row = cursor.fetchone()
    if row:
        print(f"   ✓ FOUND: {row['name']}")
    else:
        print(f"   ✗ NOT FOUND")

else:
    print(f"\n❌ Error: {data_dir} does not exist!")

print("\n" + "=" * 60)
