"""Test markdown mode data loading and matching"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


def test_markdown_loading():
    """Test loading markdown files into database"""
    print("Testing markdown data loading...")

    # Use in-memory database
    db = get_database(":memory:")

    # Load markdown data from data-md directory
    data_dir = Path(__file__).parent.parent / "data-md"

    if not data_dir.exists():
        print(f"  ⚠️  Warning: {data_dir} not found, skipping test")
        return

    load_data(db.connection, data_dir, format='markdown')

    # Check abbreviations loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
    abbr_count = cursor.fetchone()[0]
    print(f"  Loaded {abbr_count} abbreviations")

    # Check people loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM contacts")
    people_count = cursor.fetchone()[0]
    print(f"  Loaded {people_count} people")

    # Check snippets loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM snippets")
    snippet_count = cursor.fetchone()[0]
    print(f"  Loaded {snippet_count} snippets")

    # Check projects loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]
    print(f"  Loaded {project_count} projects")

    assert abbr_count > 0 or people_count > 0, "No data loaded from markdown"

    print("✓ Markdown loading passed")
    return db


def test_llm_abbreviation_match(db):
    """Test that 'llm' matches the abbreviation"""
    print("\nTesting LLM abbreviation match...")

    # Direct SQL check
    cursor = db.connection.execute("""
        SELECT abbr, full FROM abbreviations
        WHERE UPPER(abbr) = UPPER(?)
    """, ("llm",))

    row = cursor.fetchone()
    if row:
        print(f"  ✓ Found in database: {row['abbr']} = {row['full']}")
    else:
        print("  ✗ NOT found in database")
        # List all abbreviations
        cursor = db.connection.execute("SELECT abbr FROM abbreviations")
        all_abbrs = [r['abbr'] for r in cursor.fetchall()]
        print(f"  Available abbreviations: {', '.join(all_abbrs[:10])}")
        assert False, "LLM abbreviation not found"

    # Test via context analyzer
    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    result = analyzer.analyze("llm")

    if result.get('abbreviation'):
        abbr = result['abbreviation']
        print(f"  ✓ Context analyzer found: {abbr['abbr']} = {abbr['full']}")
        assert abbr['abbr'].upper() == 'LLM'
    else:
        print("  ✗ Context analyzer did NOT find abbreviation")
        print(f"  Result keys: {list(result.keys())}")
        print(f"  Exact matches: {result.get('exact_matches', [])}")
        assert False, "Context analyzer failed to find LLM"


def test_stefan_contact_match(db):
    """Test that 'Stefan' matches the contact (name from header, not filename)"""
    print("\nTesting Stefan contact match...")

    # Direct SQL check
    cursor = db.connection.execute("""
        SELECT name, email FROM contacts
        WHERE LOWER(name) LIKE LOWER(?)
    """, ("%stefan%",))

    row = cursor.fetchone()
    if row:
        print(f"  ✓ Found in database: {row['name']} ({row['email'] or 'no email'})")
    else:
        print("  ✗ NOT found in database")
        # List all contacts
        cursor = db.connection.execute("SELECT name FROM contacts")
        all_contacts = [r['name'] for r in cursor.fetchall()]
        print(f"  Available contacts: {', '.join(all_contacts)}")
        assert False, "Stefan contact not found"

    # Test via context analyzer
    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    result = analyzer.analyze("Stefan")

    exact_matches = result.get('exact_matches', [])
    contact_matches = [m for m in exact_matches if m['type'] == 'contact']

    if contact_matches:
        contact = contact_matches[0]['data']
        print(f"  ✓ Context analyzer found: {contact['name']}")
        assert contact['name'] == "Stefan Krona", f"Expected 'Stefan Krona', got '{contact['name']}'"
    else:
        print("  ✗ Context analyzer did NOT find contact")
        print(f"  Exact matches: {exact_matches}")
        assert False, "Context analyzer failed to find Stefan"


def test_case_insensitive_matching(db):
    """Test case-insensitive matching for abbreviations"""
    print("\nTesting case-insensitive matching...")

    # Test various cases
    test_cases = ["llm", "LLM", "Llm", "lLm"]

    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    for test_text in test_cases:
        result = analyzer.analyze(test_text)
        if result.get('abbreviation'):
            print(f"  ✓ '{test_text}' matched")
        else:
            print(f"  ✗ '{test_text}' did NOT match")
            assert False, f"Case-insensitive matching failed for '{test_text}'"


def main():
    """Run all markdown mode tests"""
    print("=" * 60)
    print("Markdown Mode Tests")
    print("=" * 60)

    try:
        # Test 1: Load markdown data
        db = test_markdown_loading()
        if not db:
            print("\n⚠️  Markdown data directory not found, tests skipped")
            return 0

        # Test 2: Test LLM abbreviation
        test_llm_abbreviation_match(db)

        # Test 3: Test Stefan contact (name from header, not filename)
        test_stefan_contact_match(db)

        # Test 4: Test case-insensitive matching
        test_case_insensitive_matching(db)

        print("\n" + "=" * 60)
        print("✅ All markdown mode tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
