# Acceptance Test and Refactoring Documentation

## Overview

This document describes the acceptance test implementation and the refactorings made to support user-controlled contact linking in snippets.

## Problem Statement

Previously, when saving a snippet that mentioned person names:
1. The system would **auto-detect ALL person names** in the text
2. It would **automatically link to ALL detected persons**, ignoring user selections
3. This caused issues where:
   - Snippets were linked to contacts the user didn't select
   - Newly created contacts were not properly linked
   - Duplicate linking to the same contact could occur

## Solution

Implemented a comprehensive refactoring to support **explicit person linking**, where the system respects user selections for which contacts to link to.

---

## Refactoring Details

### 1. EntitySaver.save_as_snippet() Enhancement

**File**: `context-tool/src/saver.py`
**Lines**: 216-298

#### Changes Made:

**Added Parameters:**
```python
def save_as_snippet(
    self,
    text: str,
    tags: Optional[List[str]] = None,
    source: Optional[str] = None,
    additional_info: Optional[Dict] = None,
    auto_link_persons: bool = True,              # NEW
    explicit_person_names: Optional[List[str]] = None  # NEW
) -> Path:
```

**Parameter Descriptions:**
- `auto_link_persons`: If `True`, automatically detect and link to all person names in text (default behavior)
- `explicit_person_names`: If provided, link **only** to these specific person names (user selections)

**Logic Flow:**
```python
# Link snippet to person pages based on parameters
if explicit_person_names is not None:
    # Use explicit list of person names (from user selection)
    self._link_snippet_to_explicit_persons(explicit_person_names, filepath, text)
elif auto_link_persons:
    # Auto-detect person names and link
    self._link_snippet_to_persons(text, filepath)
# else: no linking
```

**Why This Matters:**
- **Explicit control**: When user makes selections in the UI, we pass `explicit_person_names` and set `auto_link_persons=False`
- **Backward compatible**: Default behavior (`auto_link_persons=True`) preserves existing functionality
- **Flexible**: Can disable all linking by passing `auto_link_persons=False` with no explicit names

---

### 2. New Method: _link_snippet_to_explicit_persons()

**File**: `context-tool/src/saver.py`
**Lines**: 566-589

#### Implementation:

```python
def _link_snippet_to_explicit_persons(
    self,
    person_names: List[str],
    snippet_path: Path,
    snippet_text: str
):
    """
    Link snippet to explicitly specified person names (user-selected contacts)

    Args:
        person_names: List of person names to link to
        snippet_path: Path to the snippet file
        snippet_text: Text of the snippet
    """
    if not person_names:
        return

    print(f"   🔗 Linking snippet to {len(person_names)} explicitly selected person(s): {', '.join(person_names)}")

    # For each person, find their file and append snippet
    for person_name in person_names:
        if not person_name:  # Skip empty names
            continue

        person_file = self._find_person_file(person_name)
        if person_file:
            self._append_snippet_to_person_file(person_file, snippet_path, snippet_text)
        else:
            print(f"   ⚠ Person file not found for: {person_name}")
```

**Key Difference from Auto-Detection:**
- `_link_snippet_to_persons()`: Scans text with regex to find ALL person names
- `_link_snippet_to_explicit_persons()`: Uses provided list, respecting user choices

---

### 3. SmartSaver.save() Enhancement

**File**: `context-tool/src/saver.py`
**Lines**: 709-763

#### Changes Made:

**Updated Metadata Handling:**
```python
else:  # Default to snippet
    # Extract snippet-specific metadata
    tags = metadata.get('tags', [])
    source = metadata.get('source')
    explicit_person_names = metadata.get('explicit_person_names')  # NEW
    auto_link_persons = metadata.get('auto_link_persons', True)    # NEW

    result = self.saver.save_as_snippet(
        text=text,
        tags=tags,
        source=source,
        auto_link_persons=auto_link_persons,
        explicit_person_names=explicit_person_names
    )
```

**Updated Docstring:**
```python
"""
Args:
    ...
    metadata: Optional metadata dict which can include:
        - For abbreviations: {'full': '...', 'definition': '...'}
        - For snippets: {'tags': [...], 'source': '...',
                        'explicit_person_names': [...],
                        'auto_link_persons': bool}
...
"""
```

**Why This Matters:**
- SmartSaver is the interface used by the API
- Now supports passing through the new parameters
- Maintains backward compatibility

---

### 4. API Save Endpoint Update

**File**: `context-tool/src/api.py`
**Lines**: 271-299

#### Changes Made:

**Building Explicit Person Names List:**
```python
# 2. Build list of explicit person names to link to (respects user selections)
explicit_person_names = []

# Add existing contacts the user selected
for existing_contact in request.link_to_existing:
    contact_name = existing_contact.get('contact_name', '')
    if contact_name:
        explicit_person_names.append(contact_name)

# Add newly created contacts
for new_person in request.create_new_contacts:
    person_name = new_person.get('name', '')
    if person_name:
        explicit_person_names.append(person_name)
```

**Conditional Explicit Linking:**
```python
# 3. Save the snippet with explicit person linking (only link to user-selected contacts)
# If user made selections, use explicit linking; otherwise auto-detect
use_explicit = len(request.link_to_existing) > 0 or len(request.create_new_contacts) > 0

filepath = saver.save(
    text=request.text,
    save_type='snippet',
    metadata={
        'tags': request.tags,
        'source': request.source or 'web',
        'explicit_person_names': explicit_person_names if use_explicit else None,
        'auto_link_persons': not use_explicit  # Auto-link only if no explicit selections
    }
)
```

**Logic:**
- If user made smart save selections → use explicit linking with their choices
- If no selections (regular save) → fall back to auto-detection
- This fixes the bug where snippets were linked to all detected people regardless of user choices

---

## Acceptance Test

### Test File

**Location**: `context-tool/tests/test_contact_linking_acceptance.py`

### Test Scenario

The acceptance test validates the complete end-to-end workflow:

1. **Setup**: Create existing contact "Sarah Mitchell"
2. **Analysis**: Analyze text mentioning both "Sarah Mitchell" (existing) and "John Davis" (new)
3. **Verification**: Confirm both people are detected correctly with proper exists/new flags
4. **User Selection**: Simulate user selecting to:
   - Link to existing contact: Sarah Mitchell
   - Create new contact: John Davis
5. **Save**: Save snippet with smart linking
6. **Assertions**: Verify:
   - ✅ Sarah Mitchell's file has link to snippet
   - ✅ John Davis was created as new contact
   - ✅ John Davis's file has link to snippet
   - ✅ Snippet is linked to ONLY the selected contacts (not all detected names)

### Test Structure

```python
class AcceptanceTest:
    def setup(self):
        """Set up test environment with temporary directory"""

    def create_existing_contact(self, name: str, email: str = None) -> Path:
        """Create an existing contact for testing"""

    def analyze_text_with_contacts(self, text: str) -> dict:
        """Analyze text to detect people"""

    def save_snippet_with_smart_linking(
        self,
        text: str,
        link_to_existing: list = None,
        create_new_contacts: list = None
    ) -> Path:
        """Save snippet with smart contact linking"""

    def verify_contact_has_snippet_link(
        self,
        contact_name: str,
        snippet_path: Path
    ) -> bool:
        """Verify that a contact file has a link to the snippet"""

    def run_full_acceptance_test(self):
        """Run the complete acceptance test"""
```

### Running the Test

```bash
cd context-tool
python3 tests/test_contact_linking_acceptance.py
```

### Expected Output

```
======================================================================
🧪 ACCEPTANCE TEST: Contact Analysis & Smart Linking
======================================================================

📦 Setting up test environment...
   Created temp directory: /tmp/tmpXXXXXX

📋 Step 1: Create existing contact
   ✓ Created existing contact: Sarah Mitchell -> sarah-mitchell.md

📋 Step 2: Analyze text with contacts
   Text: Met with Sarah Mitchell and John Davis today....
   Detected 2 people:
      ✓ Sarah Mitchell (exists: contact_id=1)
      + John Davis (new)
   ✓ Contact detection working correctly

📋 Step 3: User selects smart linking options
   Link to existing: ['Sarah Mitchell']
   Create new: ['John Davis']

📋 Step 4: Save snippet with smart linking
   ✓ Created new contact: John Davis -> john-davis.md
   ✓ Saved snippet: 2025-01-08-met-with-sarah.md

📋 Step 5: Verify connections
   ✓ Contact 'Sarah Mitchell' has link to snippet '2025-01-08-met-with-sarah.md'
   ✓ Contact 'John Davis' has link to snippet '2025-01-08-met-with-sarah.md'

📋 Step 6: Verify new contact was created
   ✓ John Davis was created as a new contact

======================================================================
✅ ACCEPTANCE TEST PASSED!
======================================================================

✨ Summary:
   • Existing contact detected correctly
   • New contact detected correctly
   • New contact created successfully
   • Snippet linked to existing contact
   • Snippet linked to newly created contact

🎉 All acceptance criteria met!
```

---

## Benefits of This Refactoring

### 1. **User Control**
- Users can now choose exactly which contacts to link to
- No more unwanted automatic linking

### 2. **Correctness**
- Snippets are linked only to selected contacts
- New contacts are properly created and linked
- No duplicate linking

### 3. **Flexibility**
- Supports explicit linking (user selections)
- Supports automatic linking (backward compatible)
- Supports no linking (if desired)

### 4. **Testability**
- Comprehensive acceptance test validates entire workflow
- Easy to add more test scenarios
- Clear test structure for future enhancements

### 5. **Maintainability**
- Clear separation between auto-detection and explicit linking
- Well-documented parameters and behavior
- Backward compatible with existing code

---

## Related Files

### Modified Files
- `context-tool/src/saver.py` - Core refactoring
- `context-tool/src/api.py` - API integration

### New Files
- `context-tool/tests/test_contact_linking_acceptance.py` - Acceptance test
- `ACCEPTANCE_TEST_REFACTORINGS.md` - This documentation

---

## Future Enhancements

Potential improvements that could build on this refactoring:

1. **Batch Operations**: Link multiple snippets to contacts at once
2. **UI Improvements**: Show preview of which contacts will be linked before save
3. **Unlinking**: Add ability to remove snippet links from contacts
4. **Smart Suggestions**: Rank detected people by relevance/frequency
5. **Confidence Thresholds**: Only auto-link when confidence is above threshold

---

## Conclusion

This refactoring transforms the contact linking system from an automatic, all-or-nothing approach to a flexible, user-controlled system that respects selections while maintaining backward compatibility. The comprehensive acceptance test ensures the feature works correctly and provides a foundation for future testing.
