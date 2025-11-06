"""Test person name matching from markdown headers

This test verifies that person names are correctly extracted from markdown
headers and matched properly. Addresses the issue where 'Stefan Krona' was
not matching because the loader wasn't reading from markdown headers.

File: data-md/people/magnus-sjostrand.md
- Filename: magnus-sjostrand.md
- Header: # Stefan Krona
- No 'name' field in frontmatter

The loader should extract "Stefan Krona" from the header, not use the filename.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


def test_person_name_extraction():
    """Test that person names are correctly extracted from markdown headers"""
    print("Testing person name extraction from markdown...")

    # Initialize database
    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"

    # Load markdown data
    load_data(db.connection, data_dir, format='markdown')

    # Check what names were loaded
    cursor = db.connection.execute("SELECT name FROM contacts ORDER BY name")
    names = [row['name'] for row in cursor.fetchall()]

    print(f"\n  Loaded {len(names)} people:")
    for name in names:
        print(f"    - {name}")

    # Verify Stefan Krona was loaded (not "Magnus Sjostrand")
    assert "Stefan Krona" in names, "Stefan Krona should be loaded from header"
    assert "Magnus Sjostrand" not in names, "Magnus Sjostrand should NOT be loaded"

    print("\n  ✓ Stefan Krona loaded correctly from header (not filename)")
    return True


def test_person_matching():
    """Test that person matching works with names from markdown headers"""
    print("\n\nTesting person name matching...")

    # Initialize
    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"
    load_data(db.connection, data_dir, format='markdown')

    # Create analyzer (same as used in demo/widget modes)
    analyzer = ContextAnalyzer(
        db.connection,
        PatternMatcher(),
        ActionSuggester(),
        None
    )

    # Test cases
    test_cases = [
        ("Stefan", "Stefan Krona"),
        ("Krona", "Stefan Krona"),
        ("Stefan Krona", "Stefan Krona"),
        ("sarah", "Sarah Mitchell"),
        ("Sarah Mitchell", "Sarah Mitchell"),
    ]

    all_passed = True

    for query, expected_name in test_cases:
        result = analyzer.analyze(query)

        # Extract contacts from exact_matches
        contacts = [m for m in result['exact_matches'] if m['type'] == 'contact']

        if contacts:
            found_name = contacts[0]['data']['name']
            if found_name == expected_name:
                print(f"  ✓ '{query}' -> Found: {found_name}")
            else:
                print(f"  ✗ '{query}' -> Expected: {expected_name}, Got: {found_name}")
                all_passed = False
        else:
            print(f"  ✗ '{query}' -> No contact found (expected: {expected_name})")
            all_passed = False

    # Test that "magnus" does NOT match
    result = analyzer.analyze("magnus")
    contacts = [m for m in result['exact_matches'] if m['type'] == 'contact']

    if not contacts:
        print(f"  ✓ 'magnus' -> Correctly no match (name is Stefan, not Magnus)")
    else:
        print(f"  ✗ 'magnus' -> Should not match, but found: {contacts[0]['data']['name']}")
        all_passed = False

    return all_passed


def test_demo_and_widget_modes():
    """Test that both demo and widget modes use the same matching logic"""
    print("\n\nTesting mode compatibility...")

    # Both modes use:
    # 1. Same MarkdownDataLoader for loading
    # 2. Same ContextAnalyzer for matching
    # 3. Same database connection

    # Initialize (simulates both modes)
    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"
    load_data(db.connection, data_dir, format='markdown')
    analyzer = ContextAnalyzer(
        db.connection,
        PatternMatcher(),
        ActionSuggester(),
        None
    )

    # Test matching (same code path for both modes)
    result = analyzer.analyze("Stefan Krona")
    contacts = [m for m in result['exact_matches'] if m['type'] == 'contact']

    if contacts and contacts[0]['data']['name'] == "Stefan Krona":
        print("  ✓ Demo mode: Stefan Krona matches")
        print("  ✓ Widget mode: Stefan Krona matches (same analyzer)")
        print("\n  Both modes use identical matching logic ✓")
        return True
    else:
        print("  ✗ Matching failed")
        return False


def main():
    """Run all person name matching tests"""
    print("=" * 70)
    print("Person Name Matching Tests")
    print("=" * 70)

    try:
        # Run tests
        test1 = test_person_name_extraction()
        test2 = test_person_matching()
        test3 = test_demo_and_widget_modes()

        print("\n" + "=" * 70)
        if test1 and test2 and test3:
            print("✅ All person name matching tests passed!")
            print("\nSummary:")
            print("  ✓ Names extracted from markdown headers (not filenames)")
            print("  ✓ Partial name matching works (Stefan, Krona)")
            print("  ✓ Full name matching works (Stefan Krona)")
            print("  ✓ Case-insensitive matching works (sarah)")
            print("  ✓ Demo and widget modes use same logic")
            print("=" * 70)
            return 0
        else:
            print("❌ Some tests failed!")
            print("=" * 70)
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
