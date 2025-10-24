"""Basic functionality tests for Context Tool"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.data_loader import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


def test_database_initialization():
    """Test database setup"""
    print("Testing database initialization...")

    db = get_database(":memory:")
    assert db.connection is not None

    # Check tables exist
    cursor = db.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = ['contacts', 'snippets', 'projects', 'relationships', 'embeddings']
    for table in expected_tables:
        assert table in tables, f"Table {table} not found"

    print("✓ Database initialization passed")
    return db


def test_data_loading(db):
    """Test YAML data loading"""
    print("\nTesting data loading...")

    data_dir = Path(__file__).parent.parent / "data"
    load_data(db.connection, data_dir)

    # Check contacts loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM contacts")
    contact_count = cursor.fetchone()[0]
    assert contact_count > 0, "No contacts loaded"
    print(f"  Loaded {contact_count} contacts")

    # Check snippets loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM snippets")
    snippet_count = cursor.fetchone()[0]
    assert snippet_count > 0, "No snippets loaded"
    print(f"  Loaded {snippet_count} snippets")

    # Check projects loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]
    assert project_count > 0, "No projects loaded"
    print(f"  Loaded {project_count} projects")

    # Check relationships created
    cursor = db.connection.execute("SELECT COUNT(*) FROM relationships")
    rel_count = cursor.fetchone()[0]
    print(f"  Created {rel_count} relationships")

    print("✓ Data loading passed")


def test_pattern_matcher():
    """Test pattern detection"""
    print("\nTesting pattern matcher...")

    matcher = PatternMatcher()

    # Test Jira ticket detection
    result = matcher.detect("JT-344 is a bug")
    assert 'jira_ticket' in result
    assert 'JT-344' in result['jira_ticket']
    print("  ✓ Jira ticket detection")

    # Test email detection
    result = matcher.detect("Contact sarah.m@company.com")
    assert 'email' in result
    assert 'sarah.m@company.com' in result['email']
    print("  ✓ Email detection")

    # Test URL detection
    result = matcher.detect("Visit https://github.com/test")
    assert 'url' in result
    print("  ✓ URL detection")

    # Test type detection
    text_type = matcher.get_type("JT-344")
    assert text_type == 'jira_ticket'
    print("  ✓ Type detection")

    print("✓ Pattern matcher passed")


def test_context_analyzer(db):
    """Test context analysis"""
    print("\nTesting context analyzer...")

    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    # Test analyzing a Jira ticket
    result = analyzer.analyze("JT-344")

    assert result['selected_text'] == "JT-344"
    assert result['detected_type'] == 'jira_ticket'
    assert 'patterns' in result
    assert 'exact_matches' in result
    assert 'smart_context' in result
    assert 'actions' in result

    print(f"  Type detected: {result['detected_type']}")
    print(f"  Exact matches: {len(result['exact_matches'])}")
    print(f"  Actions suggested: {len(result['actions'])}")
    print(f"  Context: {result['smart_context'][:50]}...")

    print("✓ Context analyzer passed")


def test_action_suggester():
    """Test action suggestions"""
    print("\nTesting action suggester...")

    suggester = ActionSuggester()

    # Test Jira ticket actions
    actions = suggester.suggest_actions(
        "JT-344",
        "jira_ticket",
        [],
        {'jira_ticket': ['JT-344']}
    )

    assert len(actions) > 0
    action_labels = [a['label'] for a in actions]
    assert 'Open in Jira' in action_labels
    print(f"  ✓ Generated {len(actions)} actions for Jira ticket")

    # Test email actions
    actions = suggester.suggest_actions(
        "test@example.com",
        "email",
        [],
        {'email': ['test@example.com']}
    )

    action_labels = [a['label'] for a in actions]
    assert 'Send email' in action_labels
    print(f"  ✓ Generated {len(actions)} actions for email")

    print("✓ Action suggester passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Context Tool - Basic Functionality Tests")
    print("=" * 60)

    try:
        # Test 1: Database
        db = test_database_initialization()

        # Test 2: Data loading
        test_data_loading(db)

        # Test 3: Pattern matcher
        test_pattern_matcher()

        # Test 4: Action suggester
        test_action_suggester()

        # Test 5: Context analyzer
        test_context_analyzer(db)

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
