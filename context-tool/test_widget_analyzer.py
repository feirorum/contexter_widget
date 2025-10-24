"""Test that widget analyzer finds matches correctly"""

from pathlib import Path
from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer

print("=" * 60)
print("Testing Widget Mode Analyzer")
print("=" * 60)

# Simulate widget mode initialization
db_path = ":memory:"
data_dir = Path("./data-md")

print("\n1. Initialize database...")
db = get_database(db_path)

print("\n2. Load markdown data...")
load_data(db.connection, data_dir, format='markdown')

# Check data is loaded
cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
abbr_count = cursor.fetchone()[0]
print(f"   ✓ Loaded {abbr_count} abbreviations")

cursor = db.connection.execute("SELECT COUNT(*) FROM contacts")
contact_count = cursor.fetchone()[0]
print(f"   ✓ Loaded {contact_count} contacts")

print("\n3. Create analyzer (main thread)...")
matcher = PatternMatcher()
suggester = ActionSuggester()
analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)
print("   ✓ Analyzer created")

print("\n4. Test matches with SAME database connection...")

# Test LLM
print("\n   Testing 'llm':")
result = analyzer.analyze("llm")
if result.get('abbreviation'):
    print(f"   ✓ FOUND: {result['abbreviation']['abbr']} = {result['abbreviation']['full']}")
else:
    print(f"   ✗ NOT FOUND")
    print(f"   Result: {result}")

# Test API
print("\n   Testing 'api':")
result = analyzer.analyze("api")
if result.get('abbreviation'):
    print(f"   ✓ FOUND: {result['abbreviation']['abbr']} = {result['abbreviation']['full']}")
else:
    print(f"   ✗ NOT FOUND")

# Test Magnus
print("\n   Testing 'Magnus':")
result = analyzer.analyze("Magnus")
exact_matches = result.get('exact_matches', [])
contact_matches = [m for m in exact_matches if m['type'] == 'contact']
if contact_matches:
    print(f"   ✓ FOUND: {contact_matches[0]['data']['name']}")
else:
    print(f"   ✗ NOT FOUND")

print("\n5. Simulate thread behavior (OLD WAY - BROKEN)...")
print("   Creating NEW database connection in thread...")
thread_db = get_database(db_path).connection

# Check if new connection has data
cursor = thread_db.execute("SELECT COUNT(*) FROM abbreviations")
thread_abbr_count = cursor.fetchone()[0]
print(f"   Thread DB has {thread_abbr_count} abbreviations (should be 0 - EMPTY!)")

if thread_abbr_count == 0:
    print("   ✗ NEW connection is EMPTY - this is why widget had no matches!")
else:
    print("   Thread DB has data (unexpected)")

print("\n6. Simulate thread behavior (NEW WAY - FIXED)...")
print("   REUSING same analyzer from main thread...")
result = analyzer.analyze("llm")
if result.get('abbreviation'):
    print(f"   ✓ FOUND: {result['abbreviation']['abbr']} (Fixed!)")
else:
    print(f"   ✗ NOT FOUND (Still broken)")

print("\n" + "=" * 60)
print("Summary:")
print("- OLD: Thread created new DB connection → empty DB → no matches")
print("- NEW: Thread reuses same analyzer → same DB → matches work!")
print("=" * 60)
