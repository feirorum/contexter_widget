#!/usr/bin/env python3
"""Test script to demonstrate person-linking in snippets"""

from pathlib import Path
from src.saver import EntitySaver

# Initialize saver with data-md directory
data_dir = Path("./data-md")
saver = EntitySaver(data_dir)

print("=" * 60)
print("Testing Person-Linking in Snippets")
print("=" * 60)

# Test snippet that mentions a person
test_snippet = """Discussed authentication approach with Emma Rodriguez today.
She recommended using JWT with refresh tokens for the mobile app.
Will implement her suggestions in the next sprint."""

print(f"\n📝 Saving test snippet:")
print(f"   {test_snippet[:80]}...")

# Save the snippet
snippet_path = saver.save_as_snippet(
    text=test_snippet,
    tags=["auth", "meeting"],
    source="test"
)

print(f"\n✅ Snippet saved to: {snippet_path.name}")
print(f"\n🔍 Check Emma Rodriguez's file at: data-md/people/emma-rodriguez.md")
print(f"   It should now have a ## Snippets section with a link to this snippet!")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
