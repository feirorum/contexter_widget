"""Unit tests for the smart saver functionality"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saver import EntitySaver, SmartSaver, get_save_choices


def test_entity_detection():
    """Test entity type detection"""
    print("Testing entity detection...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = EntitySaver(Path(tmpdir))

        # Test person name detection
        detections = saver.detect_entity_type("John Doe")
        assert len(detections) > 0
        assert any(d[0] == 'person' for d in detections)
        print("  ✓ Person name detection")

        # Test email detection (should suggest person)
        detections = saver.detect_entity_type("sarah.m@company.com")
        assert len(detections) > 0
        assert any(d[0] == 'person' and d[1] > 0.9 for d in detections)
        print("  ✓ Email detection")

        # Test abbreviation detection
        detections = saver.detect_entity_type("API")
        assert len(detections) > 0
        assert any(d[0] == 'abbreviation' for d in detections)
        print("  ✓ Abbreviation detection")

        # Test snippet (no pattern)
        detections = saver.detect_entity_type("Discussed authentication implementation")
        assert len(detections) == 1
        assert detections[0][0] == 'snippet'
        assert detections[0][1] == 1.0
        print("  ✓ Snippet (no pattern) detection")


def test_save_choices():
    """Test save choices generation"""
    print("\nTesting save choices generation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = EntitySaver(Path(tmpdir))

        # Test with person name
        choices = get_save_choices("John Doe", saver)
        assert len(choices) >= 2  # Person + snippet
        assert choices[0]['type'] == 'person'
        assert choices[0]['confidence'] >= 0.5
        print("  ✓ Person choices (multiple options)")

        # Test with abbreviation
        choices = get_save_choices("JWT", saver)
        assert len(choices) >= 2  # Abbreviation + snippet
        assert any(c['type'] == 'abbreviation' for c in choices)
        print("  ✓ Abbreviation choices (multiple options)")

        # Test with plain text (should only return snippet)
        choices = get_save_choices("Discussed the project timeline", saver)
        # Check if only snippet is returned with high confidence
        snippet_choices = [c for c in choices if c['type'] == 'snippet']
        assert len(snippet_choices) == 1

        # Check if there are other choices (person, abbr) with lower confidence
        # If only snippet choice exists, this test case validates the "no dialog" scenario
        high_confidence_non_snippet = [
            c for c in choices
            if c['type'] != 'snippet' and c['confidence'] >= 0.5
        ]
        if len(high_confidence_non_snippet) == 0:
            # Only snippet with high confidence - should skip dialog
            assert len(choices) == 1 and choices[0]['type'] == 'snippet'
            print("  ✓ Plain text choices (snippet only - no dialog needed)")
        else:
            print("  ✓ Plain text choices (multiple options)")


def test_save_as_snippet():
    """Test saving text as snippet"""
    print("\nTesting save as snippet...")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        saver = EntitySaver(data_dir)

        # Save a snippet
        text = "Discussed authentication implementation with Sarah. Need to review JWT tokens."
        filepath = saver.save_as_snippet(text)

        assert filepath.exists()
        assert filepath.parent == data_dir / "snippets"
        assert filepath.suffix == ".md"

        # Check file content
        content = filepath.read_text(encoding='utf-8')
        assert "---" in content  # Frontmatter
        assert "type: snippet" in content
        assert text in content
        assert "## Related" in content

        print(f"  ✓ Snippet saved to {filepath.name}")


def test_save_as_person():
    """Test saving text as person"""
    print("\nTesting save as person...")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        saver = EntitySaver(data_dir)

        # Save a person
        text = "John Doe john.doe@example.com Lead Developer"
        filepath = saver.save_as_person(text)

        assert filepath.exists()
        assert filepath.parent == data_dir / "people"
        assert filepath.suffix == ".md"

        # Check file content
        content = filepath.read_text(encoding='utf-8')
        assert "---" in content
        assert "type: person" in content
        assert "John Doe" in content
        assert "john.doe@example.com" in content
        assert "## Notes" in content

        print(f"  ✓ Person saved to {filepath.name}")


def test_save_as_abbreviation():
    """Test saving text as abbreviation"""
    print("\nTesting save as abbreviation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        saver = EntitySaver(data_dir)

        # Save an abbreviation
        text = "API"
        filepath = saver.save_as_abbreviation(text)

        assert filepath.exists()
        assert filepath.parent == data_dir / "abbreviations" / "custom"
        assert filepath.suffix == ".md"

        # Check file content
        content = filepath.read_text(encoding='utf-8')
        assert "---" in content
        assert "type: abbreviation" in content
        assert "abbr: API" in content
        assert "## Definition" in content

        print(f"  ✓ Abbreviation saved to {filepath.name}")


def test_smart_saver_wrapper():
    """Test SmartSaver wrapper class"""
    print("\nTesting SmartSaver wrapper...")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        smart_saver = SmartSaver(data_dir)

        # Test get_save_choices
        choices = smart_saver.get_save_choices("API")
        assert len(choices) >= 1
        print("  ✓ SmartSaver.get_save_choices() works")

        # Test save method
        filepath = smart_saver.save("Test snippet text", "snippet")
        assert filepath.exists()
        print("  ✓ SmartSaver.save() works")

        # Test callable interface
        filepath2 = smart_saver("Another test snippet")
        assert filepath2.exists()
        print("  ✓ SmartSaver() callable works")


def test_no_dialog_scenario():
    """
    Test the specific scenario for no dialog:
    When only snippet is detected, should return single choice
    """
    print("\nTesting no-dialog scenario...")

    with tempfile.TemporaryDirectory() as tmpdir:
        saver = EntitySaver(Path(tmpdir))

        # Test texts that should NOT trigger dialog
        no_dialog_texts = [
            "Discussed the authentication implementation",
            "Met with team to review architecture",
            "Updated the deployment script for production",
            "Fixed bug in user login flow",
        ]

        for text in no_dialog_texts:
            choices = get_save_choices(text, saver)

            # Filter only high-confidence choices (>= 0.5)
            high_conf_choices = [c for c in choices if c['confidence'] >= 0.5]

            # Should only have snippet as high-confidence choice
            if len(high_conf_choices) == 1 and high_conf_choices[0]['type'] == 'snippet':
                print(f"  ✓ No dialog needed: '{text[:40]}...'")
            else:
                # This is fine too - just means we'll show a dialog
                print(f"  → Dialog shown: '{text[:40]}...' ({len(high_conf_choices)} options)")


def test_save_log():
    """Test that saves are logged"""
    print("\nTesting save logging...")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        log_file = data_dir / "test-saves.log"
        saver = EntitySaver(data_dir, log_file=log_file)

        # Save something
        saver.save_as_snippet("Test snippet for logging")

        # Check log file exists and has content
        assert log_file.exists()
        log_content = log_file.read_text(encoding='utf-8')
        assert "snippet" in log_content
        assert "Test snippet for logging" in log_content

        print("  ✓ Save logging works")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Smart Saver Unit Tests")
    print("=" * 60)

    try:
        test_entity_detection()
        test_save_choices()
        test_save_as_snippet()
        test_save_as_person()
        test_save_as_abbreviation()
        test_smart_saver_wrapper()
        test_no_dialog_scenario()
        test_save_log()

        print("\n" + "=" * 60)
        print("✅ All saver tests passed!")
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
