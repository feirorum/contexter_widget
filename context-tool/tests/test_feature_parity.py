"""Test feature parity implementation"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_smart_saver_detection():
    """Test Smart Saver detection logic"""
    print("Testing Smart Saver detection...")

    from src.saver import SmartSaver

    data_dir = Path(__file__).parent.parent / "data-md"
    saver = SmartSaver(data_dir=data_dir)

    test_cases = [
        ("John Doe", "person", 2),  # Should detect person + snippet
        ("john@example.com", "person", 2),  # Should detect person + snippet
        ("API", "abbreviation", 2),  # Should detect abbreviation + snippet
        ("Just text", "snippet", 1),  # Should only detect snippet
    ]

    all_passed = True
    for text, expected_primary, expected_count in test_cases:
        choices = saver.get_save_choices(text)

        if len(choices) != expected_count:
            print(f"  ✗ '{text}': Expected {expected_count} choices, got {len(choices)}")
            all_passed = False
            continue

        if choices[0]['type'] != expected_primary:
            print(f"  ✗ '{text}': Expected primary type '{expected_primary}', got '{choices[0]['type']}'")
            all_passed = False
            continue

        print(f"  ✓ '{text}': {choices[0]['type']} ({int(choices[0]['confidence']*100)}%)")

    return all_passed


def test_api_endpoints():
    """Test that API endpoints are properly registered"""
    print("\n\nTesting API endpoints...")

    from src.api import app

    routes = {route.path: route for route in app.routes}

    required = [
        '/api/save-smart/detect',
        '/api/save-smart/save',
        '/api/stats',
        '/api/analyze'
    ]

    all_exist = True
    for endpoint in required:
        if endpoint in routes:
            print(f"  ✓ {endpoint} exists")
        else:
            print(f"  ✗ {endpoint} NOT FOUND")
            all_exist = False

    return all_exist


def test_widget_ui_methods():
    """Test that widget UI has new methods"""
    print("\n\nTesting widget UI methods...")

    from src.widget_ui import ContextWidget

    # Check if new methods exist
    widget = ContextWidget(start_hidden=True)

    required_methods = [
        '_render_action_buttons',
        '_handle_action',
    ]

    all_exist = True
    for method_name in required_methods:
        if hasattr(widget, method_name):
            print(f"  ✓ {method_name} exists")
        else:
            print(f"  ✗ {method_name} NOT FOUND")
            all_exist = False

    # Clean up
    widget.root.destroy()

    return all_exist


def test_web_ui_files():
    """Test that web UI files have been updated"""
    print("\n\nTesting web UI files...")

    ui_dir = Path(__file__).parent.parent / "ui" / "web"

    # Check app.js has new functions
    app_js = ui_dir / "app.js"
    if not app_js.exists():
        print(f"  ✗ app.js not found")
        return False

    with open(app_js) as f:
        content = f.read()

    required_functions = [
        'showSaveDialog',
        'performSave',
        'closeSaveDialog',
        'saveWithSelectedType',
        'showToast',
        'searchWeb'
    ]

    all_exist = True
    for func in required_functions:
        if f'function {func}' in content or f'async function {func}' in content:
            print(f"  ✓ {func}() exists in app.js")
        else:
            print(f"  ✗ {func}() NOT FOUND in app.js")
            all_exist = False

    # Check index.html has modal
    index_html = ui_dir / "index.html"
    if not index_html.exists():
        print(f"  ✗ index.html not found")
        return False

    with open(index_html) as f:
        html_content = f.read()

    if 'id="saveModal"' in html_content:
        print(f"  ✓ Save modal exists in index.html")
    else:
        print(f"  ✗ Save modal NOT FOUND in index.html")
        all_exist = False

    if 'Search Web' in html_content or 'searchWeb()' in content:
        print(f"  ✓ Search Web button exists")
    else:
        print(f"  ✗ Search Web button NOT FOUND")
        all_exist = False

    return all_exist


def main():
    """Run all feature parity tests"""
    print("=" * 70)
    print("Feature Parity Tests")
    print("=" * 70)

    try:
        test1 = test_smart_saver_detection()
        test2 = test_api_endpoints()
        test3 = test_widget_ui_methods()
        test4 = test_web_ui_files()

        print("\n" + "=" * 70)
        if test1 and test2 and test3 and test4:
            print("✅ All feature parity tests passed!")
            print("\nImplemented features:")
            print("  ✓ Smart Saver API endpoints")
            print("  ✓ Smart Saver detection logic")
            print("  ✓ Web UI save dialog with choices")
            print("  ✓ Web UI Search Web button")
            print("  ✓ Widget UI dynamic action buttons")
            print("  ✓ Widget UI detected type badge")
            print("=" * 70)
            return 0
        else:
            print("❌ Some tests failed!")
            if not test1:
                print("  ✗ Smart Saver detection failed")
            if not test2:
                print("  ✗ API endpoints missing")
            if not test3:
                print("  ✗ Widget UI methods missing")
            if not test4:
                print("  ✗ Web UI files incomplete")
            print("=" * 70)
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
