"""Test abbreviation save with custom fields"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saver import SmartSaver


def test_abbreviation_without_metadata():
    """Test saving abbreviation without metadata (backward compatibility)"""
    print("Testing abbreviation save without metadata...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = SmartSaver(data_dir=Path(tmpdir))

        # Save without metadata
        result = saver.save('API', 'abbreviation', None)

        # Read content
        content = result.read_text()

        # Verify structure
        assert '---' in content, "Should have frontmatter"
        assert 'abbr: API' in content, "Should have abbreviation in frontmatter"
        assert 'Add definition here' in content, "Should have placeholder text"

        print(f"  ✓ Saved to: {result.name}")
        print(f"  ✓ Has placeholder text")
        return True


def test_abbreviation_with_metadata():
    """Test saving abbreviation with full term and definition"""
    print("\nTesting abbreviation save with metadata...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = SmartSaver(data_dir=Path(tmpdir))

        # Save with metadata
        metadata = {
            'full': 'Representational State Transfer',
            'definition': 'An architectural style for designing networked applications using HTTP'
        }
        result = saver.save('REST', 'abbreviation', metadata)

        # Read content
        content = result.read_text()

        # Verify structure
        assert '---' in content, "Should have frontmatter"
        assert 'abbr: REST' in content, "Should have abbreviation"
        assert 'full: Representational State Transfer' in content, "Should have full term in frontmatter"
        assert 'architectural style' in content, "Should have definition in body"
        assert 'Add definition here' not in content, "Should NOT have placeholder"
        assert '# REST - Representational State Transfer' in content, "Should have title with full term"

        print(f"  ✓ Saved to: {result.name}")
        print(f"  ✓ Has full term: Representational State Transfer")
        print(f"  ✓ Has custom definition")
        print(f"  ✓ No placeholder text")
        return True


def test_abbreviation_partial_metadata():
    """Test saving abbreviation with only full term (no definition)"""
    print("\nTesting abbreviation save with partial metadata...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = SmartSaver(data_dir=Path(tmpdir))

        # Save with only full term
        metadata = {
            'full': 'Hypertext Transfer Protocol'
        }
        result = saver.save('HTTP', 'abbreviation', metadata)

        # Read content
        content = result.read_text()

        # Verify structure
        assert 'full: Hypertext Transfer Protocol' in content, "Should have full term"
        assert 'Add definition here' in content, "Should have placeholder for definition"
        assert '# HTTP - Hypertext Transfer Protocol' in content, "Should have title with full term"

        print(f"  ✓ Saved to: {result.name}")
        print(f"  ✓ Has full term")
        print(f"  ✓ Has placeholder for definition")
        return True


def test_web_ui_integration():
    """Test that web UI can properly format metadata"""
    print("\nTesting web UI metadata format...")

    # Simulate what web UI sends
    metadata = {
        'full': 'Application Programming Interface',
        'definition': 'A set of protocols and tools for building software applications'
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = SmartSaver(data_dir=Path(tmpdir))
        result = saver.save('API', 'abbreviation', metadata)

        content = result.read_text()

        # Verify all expected parts
        assert 'API' in content
        assert 'Application Programming Interface' in content
        assert 'protocols and tools' in content

        print(f"  ✓ Web UI metadata format works correctly")
        return True


def main():
    """Run all abbreviation field tests"""
    print("=" * 70)
    print("Abbreviation Fields Tests")
    print("=" * 70)

    try:
        test1 = test_abbreviation_without_metadata()
        test2 = test_abbreviation_with_metadata()
        test3 = test_abbreviation_partial_metadata()
        test4 = test_web_ui_integration()

        print("\n" + "=" * 70)
        if test1 and test2 and test3 and test4:
            print("✅ All abbreviation field tests passed!")
            print("\nVerified features:")
            print("  ✓ Backward compatibility (no metadata)")
            print("  ✓ Full metadata (full term + definition)")
            print("  ✓ Partial metadata (only full term)")
            print("  ✓ Web UI integration")
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
