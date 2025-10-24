# Data Loaders Refactoring

## Summary

Refactored data loading code into a clean, modular structure with a unified interface for loading both YAML and Markdown data formats.

## Changes Made

### 1. New Directory Structure

```
src/
└── data_loaders/
    ├── __init__.py                    # Factory function and exports
    ├── yaml_data_loader.py            # YAML data loader (was data_loader.py)
    └── markdown_data_loader.py        # Markdown data loader (was markdown_loader.py)
```

### 2. Renamed Classes

- `DataLoader` → `YAMLDataLoader` (in yaml_data_loader.py)
- `MarkdownLoader` → `MarkdownDataLoader` (in markdown_data_loader.py)

### 3. Unified Interface

Created a single `load_data()` function that handles both formats:

```python
from src.data_loaders import load_data

# Load YAML data
load_data(db.connection, Path('./data'), format='yaml')

# Load Markdown data
load_data(db.connection, Path('./data-md'), format='markdown')
```

**Old way (deprecated but still works):**
```python
from src.data_loader import load_data  # YAML
from src.markdown_loader import load_markdown_data  # Markdown
```

**New way (recommended):**
```python
from src.data_loaders import load_data

load_data(db, data_dir, format='yaml')      # or
load_data(db, data_dir, format='markdown')
```

### 4. Updated Files

All imports updated across the codebase:

- ✅ `src/api.py` - API initialization
- ✅ `src/widget_mode.py` - Widget mode
- ✅ `tests/test_basic_functionality.py` - YAML tests
- ✅ `tests/test_markdown_mode.py` - Markdown tests
- ✅ `debug_markdown.py` - Debug script

### 5. Backward Compatibility

The old files (`src/data_loader.py` and `src/markdown_loader.py`) are still present but deprecated. Use the new `src/data_loaders` module instead.

## Benefits

1. **Better Organization** - All data loaders in one module
2. **Unified Interface** - Single function with `format` parameter
3. **Type Safety** - `DataFormat` type hint for 'yaml' | 'markdown'
4. **Easy to Extend** - Add new formats (JSON, TOML, etc.) easily
5. **Clear Naming** - Classes clearly indicate what they load

## Usage Examples

### Basic Usage

```python
from src.database import get_database
from src.data_loaders import load_data

db = get_database(':memory:')

# Load YAML data
load_data(db.connection, Path('./data'), format='yaml')

# Load Markdown data
load_data(db.connection, Path('./data-md'), format='markdown')
```

### With Configuration

```python
# In main.py or api.py
if use_markdown:
    load_data(db, data_dir, format='markdown')
else:
    load_data(db, data_dir, format='yaml')
```

### Direct Class Usage (Advanced)

```python
from src.data_loaders import YAMLDataLoader, MarkdownDataLoader

# Create loader instances directly
yaml_loader = YAMLDataLoader(db.connection)
yaml_loader.load_from_yaml(Path('./data'))

md_loader = MarkdownDataLoader(db.connection)
md_loader.load_from_markdown(Path('./data-md'))
```

## Testing

All tests pass with the new structure:

```bash
# Test YAML loading
./venv/bin/python3 tests/test_basic_functionality.py

# Test Markdown loading
./venv/bin/python3 tests/test_markdown_mode.py

# Test all
./venv/bin/python3 tests/test_saver.py
./venv/bin/python3 tests/test_config_markdown.py
```

## Migration Guide

### If you're using the old imports:

**Before:**
```python
from src.data_loader import load_data
from src.markdown_loader import load_markdown_data

load_data(db, yaml_dir)
load_markdown_data(db, md_dir)
```

**After:**
```python
from src.data_loaders import load_data

load_data(db, yaml_dir, format='yaml')
load_data(db, md_dir, format='markdown')
```

### If you're using the old classes:

**Before:**
```python
from src.data_loader import DataLoader
from src.markdown_loader import MarkdownLoader

loader = DataLoader(db)
md_loader = MarkdownLoader(db)
```

**After:**
```python
from src.data_loaders import YAMLDataLoader, MarkdownDataLoader

loader = YAMLDataLoader(db)
md_loader = MarkdownDataLoader(db)
```

## Future Enhancements

With this structure, it's easy to add new data formats:

1. Create `src/data_loaders/json_data_loader.py`
2. Add `JSONDataLoader` class
3. Update `__init__.py` to support `format='json'`
4. Done!

Example:
```python
# Future: Add JSON support
load_data(db, Path('./data-json'), format='json')
```

## Notes

- Old files (`src/data_loader.py`, `src/markdown_loader.py`) can be removed in a future cleanup
- The `format` parameter defaults to `'yaml'` for backward compatibility
- All existing functionality preserved - no breaking changes
