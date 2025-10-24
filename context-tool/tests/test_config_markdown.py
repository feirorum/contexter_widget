"""Test markdown config and auto-selection"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config_files_exist():
    """Test that both config files exist"""
    print("Testing config files exist...")

    config_yaml = Path("config.yaml")
    config_markdown = Path("config-markdown.yaml")

    assert config_yaml.exists(), "config.yaml not found"
    print("  ✓ config.yaml exists")

    assert config_markdown.exists(), "config-markdown.yaml not found"
    print("  ✓ config-markdown.yaml exists")


def test_config_yaml_content():
    """Test that config.yaml uses data/ directory"""
    print("\nTesting config.yaml content...")

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    assert config['data']['directory'] == './data'
    print("  ✓ config.yaml uses ./data directory")


def test_config_markdown_content():
    """Test that config-markdown.yaml uses data-md/ directory"""
    print("\nTesting config-markdown.yaml content...")

    with open("config-markdown.yaml") as f:
        config = yaml.safe_load(f)

    assert config['data']['directory'] == './data-md'
    print("  ✓ config-markdown.yaml uses ./data-md directory")

    if 'format' in config['data']:
        assert config['data']['format'] == 'markdown'
        print("  ✓ config-markdown.yaml specifies markdown format")


def test_data_directories_exist():
    """Test that both data directories exist"""
    print("\nTesting data directories exist...")

    data_dir = Path("./data")
    data_md_dir = Path("./data-md")

    assert data_dir.exists(), "./data directory not found"
    print("  ✓ ./data directory exists")

    assert data_md_dir.exists(), "./data-md directory not found"
    print("  ✓ ./data-md directory exists")


def test_markdown_data_structure():
    """Test that data-md has correct structure"""
    print("\nTesting data-md structure...")

    data_md = Path("./data-md")

    # Check subdirectories
    assert (data_md / "people").exists(), "data-md/people not found"
    print("  ✓ data-md/people exists")

    assert (data_md / "abbreviations").exists(), "data-md/abbreviations not found"
    print("  ✓ data-md/abbreviations exists")

    # Check for sample files
    llm_file = data_md / "abbreviations" / "ai-ml" / "llm.md"
    if llm_file.exists():
        print("  ✓ Sample file found: abbreviations/ai-ml/llm.md")

    magnus_file = data_md / "people" / "magnus-sjostrand.md"
    if magnus_file.exists():
        print("  ✓ Sample file found: people/magnus-sjostrand.md")


def test_auto_config_selection():
    """Test auto-selection logic"""
    print("\nTesting auto-config selection logic...")

    # Simulate the auto-selection logic from main.py
    class Args:
        markdown = True
        config = 'config.yaml'

    args = Args()

    if args.markdown and args.config == 'config.yaml':
        config_markdown = Path('config-markdown.yaml')
        if config_markdown.exists():
            selected_config = 'config-markdown.yaml'
            print(f"  ✓ Would auto-select: {selected_config}")
        else:
            print("  ✗ config-markdown.yaml not found for auto-selection")
            assert False
    else:
        print("  → No auto-selection (using specified config)")


def main():
    """Run all config tests"""
    print("=" * 60)
    print("Config and Markdown Mode Tests")
    print("=" * 60)

    try:
        test_config_files_exist()
        test_config_yaml_content()
        test_config_markdown_content()
        test_data_directories_exist()
        test_markdown_data_structure()
        test_auto_config_selection()

        print("\n" + "=" * 60)
        print("✅ All config tests passed!")
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
