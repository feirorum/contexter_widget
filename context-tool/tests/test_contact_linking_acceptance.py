#!/usr/bin/env python3
"""
Acceptance test for the contact analysis and smart linking feature

This test validates the full end-to-end workflow:
1. Analyze text with both known and unknown contacts
2. Create new contacts as specified by user
3. Link snippet to both existing and newly created contacts
4. Verify all connections are properly established
"""

import sys
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saver import EntitySaver
from src.context_analyzer import ContextAnalyzer
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.data_loaders import load_data
from src.database import get_database


class AcceptanceTest:
    """Acceptance test runner for contact linking feature"""

    def __init__(self):
        self.tmpdir = None
        self.data_dir = None
        self.saver = None
        self.analyzer = None
        self.db = None

    def setup(self):
        """Set up test environment with temporary directory"""
        print("\n📦 Setting up test environment...")
        self.tmpdir = tempfile.mkdtemp()
        self.data_dir = Path(self.tmpdir)
        self.saver = EntitySaver(self.data_dir)

        # Initialize database with schema
        db_wrapper = get_database(':memory:')
        self.db = db_wrapper.connection

        # Load data to database (this will be empty initially)
        load_data(self.db, self.data_dir, format='markdown')

        # Initialize analyzer components
        pattern_matcher = PatternMatcher()
        action_suggester = ActionSuggester()

        self.analyzer = ContextAnalyzer(
            db=self.db,
            pattern_matcher=pattern_matcher,
            action_suggester=action_suggester
        )

        print(f"   Created temp directory: {self.tmpdir}")

    def teardown(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        if self.db:
            self.db.close()
        if self.tmpdir:
            import shutil
            shutil.rmtree(self.tmpdir)
            print("   ✓ Temporary directory removed")

    def create_existing_contact(self, name: str, email: str = None) -> Path:
        """
        Create an existing contact for testing

        Args:
            name: Contact name
            email: Optional email address

        Returns:
            Path to created contact file
        """
        text = name
        if email:
            text += f" {email}"

        filepath = self.saver.save_as_person(text)
        print(f"   ✓ Created existing contact: {name} -> {filepath.name}")

        # Reload database so analyzer can see the new contact
        load_data(self.db, self.data_dir, format='markdown')

        return filepath

    def analyze_text_with_contacts(self, text: str) -> dict:
        """
        Analyze text to detect people

        Args:
            text: Text to analyze

        Returns:
            Analysis result dictionary
        """
        result = self.analyzer.analyze(text)
        return result

    def save_snippet_with_smart_linking(
        self,
        text: str,
        link_to_existing: list = None,
        create_new_contacts: list = None
    ) -> Path:
        """
        Save snippet with smart contact linking

        Args:
            text: Snippet text
            link_to_existing: List of existing contacts to link to
            create_new_contacts: List of new contact names to create

        Returns:
            Path to saved snippet file
        """
        link_to_existing = link_to_existing or []
        create_new_contacts = create_new_contacts or []

        # First, create new contacts
        created_contact_files = []
        for new_contact in create_new_contacts:
            contact_name = new_contact.get('name', '')
            if contact_name:
                person_file = self.saver.save_as_person(contact_name)
                created_contact_files.append(person_file)
                print(f"   ✓ Created new contact: {contact_name} -> {person_file.name}")

        # Collect all person names to link to (existing + newly created)
        person_names_to_link = []

        # Add existing contacts
        for existing in link_to_existing:
            person_names_to_link.append(existing.get('contact_name', ''))

        # Add newly created contacts
        for new_contact in create_new_contacts:
            person_names_to_link.append(new_contact.get('name', ''))

        # Save snippet with explicit person linking
        snippet_file = self.saver.save_as_snippet(
            text=text,
            tags=[],
            source='acceptance_test',
            auto_link_persons=False,  # Don't auto-detect
            explicit_person_names=person_names_to_link
        )

        print(f"   ✓ Saved snippet: {snippet_file.name}")
        return snippet_file

    def verify_contact_has_snippet_link(self, contact_name: str, snippet_path: Path) -> bool:
        """
        Verify that a contact file has a link to the snippet

        Args:
            contact_name: Name of the contact
            snippet_path: Path to the snippet file

        Returns:
            True if link exists, False otherwise
        """
        # Find the contact file
        people_dir = self.data_dir / "people"
        if not people_dir.exists():
            return False

        # Search for contact file
        contact_file = None
        for file in people_dir.glob("*.md"):
            content = file.read_text(encoding='utf-8')
            if contact_name in content:
                contact_file = file
                break

        if not contact_file:
            print(f"   ✗ Contact file not found for: {contact_name}")
            return False

        # Check if snippet is linked
        content = contact_file.read_text(encoding='utf-8')
        snippet_name = snippet_path.stem

        if snippet_name in content or str(snippet_path.name) in content:
            print(f"   ✓ Contact '{contact_name}' has link to snippet '{snippet_path.name}'")
            return True
        else:
            print(f"   ✗ Contact '{contact_name}' does NOT have link to snippet")
            print(f"      Looking for: {snippet_name} or {snippet_path.name}")
            print(f"      In file: {contact_file}")
            return False

    def run_full_acceptance_test(self):
        """
        Run the complete acceptance test

        Scenario:
        1. Create existing contact "Sarah Mitchell"
        2. Analyze text mentioning both "Sarah Mitchell" (existing) and "John Davis" (new)
        3. User selects to link to Sarah and create John
        4. Save snippet with smart linking
        5. Verify snippet is linked to both contacts
        """
        print("\n" + "=" * 70)
        print("🧪 ACCEPTANCE TEST: Contact Analysis & Smart Linking")
        print("=" * 70)

        try:
            self.setup()

            # Step 1: Create existing contact
            print("\n📋 Step 1: Create existing contact")
            sarah_file = self.create_existing_contact(
                "Sarah Mitchell",
                "sarah.m@company.com"
            )

            # Step 2: Analyze text with both known and unknown contacts
            print("\n📋 Step 2: Analyze text with contacts")
            test_text = """Met with Sarah Mitchell and John Davis today.
Sarah suggested implementing the new authentication flow.
John will handle the database migration."""

            print(f"   Text: {test_text[:80]}...")
            analysis_result = self.analyze_text_with_contacts(test_text)

            # Verify detected people
            detected_people = analysis_result.get('detected_people', [])
            print(f"   Detected {len(detected_people)} people:")

            existing_people = [p for p in detected_people if p.get('exists')]
            new_people = [p for p in detected_people if not p.get('exists')]

            for person in existing_people:
                print(f"      ✓ {person['name']} (exists: contact_id={person.get('contact_id')})")

            for person in new_people:
                print(f"      + {person['name']} (new)")

            # Verify we detected both people correctly
            assert len(detected_people) >= 2, f"Expected 2+ people, found {len(detected_people)}"
            assert any(p['name'] == 'Sarah Mitchell' and p['exists'] for p in detected_people), \
                "Sarah Mitchell should be detected as existing"
            assert any(p['name'] == 'John Davis' and not p['exists'] for p in detected_people), \
                "John Davis should be detected as new"

            print("   ✓ Contact detection working correctly")

            # Step 3: User selects to link to Sarah and create John
            print("\n📋 Step 3: User selects smart linking options")

            # Simulate user selections
            sarah = next(p for p in detected_people if p['name'] == 'Sarah Mitchell')
            john = next(p for p in detected_people if p['name'] == 'John Davis')

            link_to_existing = [{
                'name': sarah['name'],
                'contact_id': sarah.get('contact_id'),
                'contact_name': sarah.get('contact_name', sarah['name'])
            }]

            create_new_contacts = [{
                'name': john['name']
            }]

            print(f"   Link to existing: {[p['name'] for p in link_to_existing]}")
            print(f"   Create new: {[p['name'] for p in create_new_contacts]}")

            # Step 4: Save snippet with smart linking
            print("\n📋 Step 4: Save snippet with smart linking")
            snippet_file = self.save_snippet_with_smart_linking(
                text=test_text,
                link_to_existing=link_to_existing,
                create_new_contacts=create_new_contacts
            )

            # Step 5: Verify all connections
            print("\n📋 Step 5: Verify connections")

            sarah_linked = self.verify_contact_has_snippet_link("Sarah Mitchell", snippet_file)
            john_linked = self.verify_contact_has_snippet_link("John Davis", snippet_file)

            # Assertions
            assert sarah_linked, "Sarah Mitchell should be linked to snippet"
            assert john_linked, "John Davis should be linked to snippet"

            # Step 6: Verify John was created as a new contact
            print("\n📋 Step 6: Verify new contact was created")
            people_dir = self.data_dir / "people"
            john_file_exists = any(
                'John Davis' in f.read_text(encoding='utf-8')
                for f in people_dir.glob("*.md")
            )

            assert john_file_exists, "John Davis contact file should exist"
            print("   ✓ John Davis was created as a new contact")

            print("\n" + "=" * 70)
            print("✅ ACCEPTANCE TEST PASSED!")
            print("=" * 70)
            print("\n✨ Summary:")
            print("   • Existing contact detected correctly")
            print("   • New contact detected correctly")
            print("   • New contact created successfully")
            print("   • Snippet linked to existing contact")
            print("   • Snippet linked to newly created contact")
            print("\n🎉 All acceptance criteria met!")

            return True

        except AssertionError as e:
            print("\n" + "=" * 70)
            print(f"❌ ACCEPTANCE TEST FAILED: {e}")
            print("=" * 70)
            import traceback
            traceback.print_exc()
            return False

        except Exception as e:
            print("\n" + "=" * 70)
            print(f"❌ ERROR: {e}")
            print("=" * 70)
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.teardown()


def main():
    """Run acceptance test"""
    test = AcceptanceTest()
    success = test.run_full_acceptance_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
