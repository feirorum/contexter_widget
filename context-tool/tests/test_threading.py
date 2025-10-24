"""Test SQLite threading behavior with check_same_thread=False"""

import sys
import threading
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


def test_cross_thread_reads():
    """Test that database can be read from different threads"""
    print("Testing cross-thread database reads...")

    # Main thread: Initialize database and analyzer
    print("\n1. Main thread: Initialize database")
    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"

    if not data_dir.exists():
        print("  ⚠️  data-md not found, using data/")
        data_dir = Path(__file__).parent.parent / "data"
        load_data(db.connection, data_dir, format='yaml')
    else:
        load_data(db.connection, data_dir, format='markdown')

    cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
    count = cursor.fetchone()[0]
    print(f"   ✓ Main thread loaded {count} abbreviations")

    print("\n2. Main thread: Create analyzer")
    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, None)

    # Test in main thread first
    print("\n3. Main thread: Test analyze")
    result = analyzer.analyze("api")
    if result.get('abbreviation'):
        print(f"   ✓ Main thread found: {result['abbreviation']['abbr']}")
    else:
        print(f"   ✗ Main thread didn't find match")
        return False

    # Now test from a different thread
    print("\n4. Background thread: Test analyze")
    thread_result = {'success': False, 'error': None}

    def thread_analyze():
        try:
            # This should work now with check_same_thread=False
            result = analyzer.analyze("llm")
            if result.get('abbreviation'):
                thread_result['success'] = True
                thread_result['abbr'] = result['abbreviation']['abbr']
                thread_result['full'] = result['abbreviation']['full']
            else:
                thread_result['error'] = "No match found"
        except Exception as e:
            thread_result['error'] = str(e)

    thread = threading.Thread(target=thread_analyze)
    thread.start()
    thread.join(timeout=5)

    if thread_result['success']:
        print(f"   ✓ Background thread found: {thread_result['abbr']} = {thread_result['full']}")
    elif thread_result['error']:
        print(f"   ✗ Background thread error: {thread_result['error']}")
        return False
    else:
        print(f"   ✗ Background thread timeout")
        return False

    return True


def test_concurrent_reads():
    """Test multiple threads reading simultaneously"""
    print("\n\nTesting concurrent reads from multiple threads...")

    # Setup
    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"

    if not data_dir.exists():
        data_dir = Path(__file__).parent.parent / "data"
        load_data(db.connection, data_dir, format='yaml')
    else:
        load_data(db.connection, data_dir, format='markdown')

    analyzer = ContextAnalyzer(
        db.connection,
        PatternMatcher(),
        ActionSuggester(),
        None
    )

    # Test concurrent reads
    results = {'errors': [], 'successes': 0}
    queries = ['api', 'llm', 'jwt', 'asap']

    def thread_query(query):
        try:
            result = analyzer.analyze(query)
            if result.get('abbreviation'):
                results['successes'] += 1
            else:
                results['errors'].append(f"{query}: No match")
        except Exception as e:
            results['errors'].append(f"{query}: {str(e)}")

    print(f"\n   Launching {len(queries)} concurrent threads...")
    threads = [threading.Thread(target=thread_query, args=(q,)) for q in queries]

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=5)

    print(f"   ✓ {results['successes']} successful reads")
    if results['errors']:
        print(f"   ✗ {len(results['errors'])} errors:")
        for error in results['errors']:
            print(f"      - {error}")
        return False

    return True


def main():
    """Run all threading tests"""
    print("=" * 60)
    print("SQLite Threading Tests")
    print("=" * 60)

    try:
        # Test 1: Cross-thread reads
        success1 = test_cross_thread_reads()

        # Test 2: Concurrent reads
        success2 = test_concurrent_reads()

        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ All threading tests passed!")
            print("\nSQLite check_same_thread=False is working correctly:")
            print("  ✓ Can read from different threads")
            print("  ✓ Can handle concurrent reads")
            print("  ✓ No ProgrammingError exceptions")
        else:
            print("❌ Some threading tests failed!")
            if not success1:
                print("  ✗ Cross-thread reads failed")
            if not success2:
                print("  ✗ Concurrent reads failed")
        print("=" * 60)

        return 0 if (success1 and success2) else 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
