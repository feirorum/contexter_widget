"""Test the refactored data_loaders module"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.data_loaders import load_data, YAMLDataLoader, MarkdownDataLoader


def test_unified_interface_yaml():
    """Test loading YAML data with unified interface"""
    print("Testing unified interface with YAML...")

    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data"

    # Load using unified interface
    load_data(db.connection, data_dir, format='yaml')

    # Verify data loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
    count = cursor.fetchone()[0]
    assert count > 0, "No abbreviations loaded"
    print(f"  ✓ Loaded {count} abbreviations via unified interface (YAML)")


def test_unified_interface_markdown():
    """Test loading Markdown data with unified interface"""
    print("\nTesting unified interface with Markdown...")

    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"

    if not data_dir.exists():
        print("  ⚠️  data-md not found, skipping")
        return

    # Load using unified interface
    load_data(db.connection, data_dir, format='markdown')

    # Verify data loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
    count = cursor.fetchone()[0]
    assert count > 0, "No abbreviations loaded"
    print(f"  ✓ Loaded {count} abbreviations via unified interface (Markdown)")


def test_yaml_loader_class():
    """Test YAMLDataLoader class directly"""
    print("\nTesting YAMLDataLoader class...")

    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data"

    loader = YAMLDataLoader(db.connection)
    loader.load_from_yaml(data_dir)

    # Verify data loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM contacts")
    count = cursor.fetchone()[0]
    assert count > 0, "No contacts loaded"
    print(f"  ✓ Loaded {count} contacts via YAMLDataLoader class")


def test_markdown_loader_class():
    """Test MarkdownDataLoader class directly"""
    print("\nTesting MarkdownDataLoader class...")

    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data-md"

    if not data_dir.exists():
        print("  ⚠️  data-md not found, skipping")
        return

    loader = MarkdownDataLoader(db.connection)
    loader.load_from_markdown(data_dir)

    # Verify data loaded
    cursor = db.connection.execute("SELECT COUNT(*) FROM contacts")
    count = cursor.fetchone()[0]
    assert count > 0, "No contacts loaded"
    print(f"  ✓ Loaded {count} people via MarkdownDataLoader class")


def test_invalid_format():
    """Test that invalid format raises error"""
    print("\nTesting invalid format handling...")

    db = get_database(":memory:")
    data_dir = Path(".")

    try:
        load_data(db.connection, data_dir, format='invalid')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported data format" in str(e)
        print("  ✓ Correctly raises ValueError for invalid format")


def test_default_format():
    """Test that default format is YAML"""
    print("\nTesting default format (should be YAML)...")

    db = get_database(":memory:")
    data_dir = Path(__file__).parent.parent / "data"

    # Load without specifying format (should default to YAML)
    load_data(db.connection, data_dir)

    # Verify YAML data loaded (133 abbreviations in YAML data)
    cursor = db.connection.execute("SELECT COUNT(*) FROM abbreviations")
    count = cursor.fetchone()[0]
    assert count > 100, f"Expected YAML data (>100 abbrs), got {count}"
    print(f"  ✓ Default format loads YAML data ({count} abbreviations)")


def main():
    """Run all data loader tests"""
    print("=" * 60)
    print("Data Loaders Module Tests")
    print("=" * 60)

    try:
        test_unified_interface_yaml()
        test_unified_interface_markdown()
        test_yaml_loader_class()
        test_markdown_loader_class()
        test_invalid_format()
        test_default_format()

        print("\n" + "=" * 60)
        print("✅ All data loader tests passed!")
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
