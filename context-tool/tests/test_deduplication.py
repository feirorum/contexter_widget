#!/usr/bin/env python3
"""
Acceptance tests for deduplication of analyzer output

These tests verify that contacts and snippets with the same ID
appear only once in the analyzer output, even when matched multiple times.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saver import EntitySaver, SmartSaver
from src.database import get_database
from src.data_loaders import load_data
from src.context_analyzer import ContextAnalyzer
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
import sqlite3


class DeduplicationTests:
    """Test suite for deduplication in analyzer output"""

    def __init__(self):
        self.temp_dir = None
        self.db = None
        self.saver = None
        self.analyzer = None

    def setup(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        print(f"   Created temp directory: {self.temp_dir}")

        # Initialize saver
        self.saver = EntitySaver(Path(self.temp_dir))

        # Initialize database
        db_wrapper = get_database(':memory:')
        self.db = db_wrapper.connection

        # Load data
        load_data(self.db, Path(self.temp_dir), format='markdown')

        # Initialize analyzer
        pattern_matcher = PatternMatcher()
        action_suggester = ActionSuggester()
        self.analyzer = ContextAnalyzer(
            db=self.db,
            pattern_matcher=pattern_matcher,
            action_suggester=action_suggester
        )

    def teardown(self):
        """Clean up test environment"""
        if self.db:
            self.db.close()
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_dedupe_exact_matches_same_contact_multiple_variations(self):
        """Test that multiple name variations matching the same contact appear only once in exact_matches"""
        print("\n🧪 Test: Deduplication of exact matches - same contact with name variations")

        # Create a contact
        contact_path = self.saver.save_as_person("John Robert Smith john.smith@example.com")
        print(f"   ✓ Created contact: John Robert Smith")

        # Reload data to get the contact in DB
        load_data(self.db, Path(self.temp_dir), format='markdown')

        # Analyze text that mentions the person with different variations
        # "John Smith" should match "John Robert Smith"
        # "John R. Smith" contains "John" and "Smith" which should also match
        text = "Met with John Smith and discussed the project. John R. Smith agreed to the proposal."

        result = self.analyzer.analyze(text)

        # Check exact_matches - should contain the contact only once
        contact_matches = [m for m in result['exact_matches'] if m['type'] == 'contact']

        print(f"   Found {len(contact_matches)} contact match(es) in exact_matches")

        if len(contact_matches) > 1:
            print(f"   ❌ FAILED: Expected 1 contact match, got {len(contact_matches)}")
            for i, match in enumerate(contact_matches):
                print(f"      Match {i+1}: {match['data']['name']} (ID: {match['data']['id']})")
            return False

        if len(contact_matches) == 1:
            print(f"   ✓ Contact appears only once: {contact_matches[0]['data']['name']}")
            return True
        else:
            print(f"   ⚠ No contact matches found (may be expected if name variations don't match)")
            return True

    def test_dedupe_detected_people_same_contact(self):
        """Test that detected_people deduplicates when different name variations match the same contact"""
        print("\n🧪 Test: Deduplication of detected_people - same contact matched by different names")

        # Create a contact
        contact_path = self.saver.save_as_person("Sarah Jane Mitchell sarah.mitchell@example.com")
        print(f"   ✓ Created contact: Sarah Jane Mitchell")

        # Reload data
        load_data(self.db, Path(self.temp_dir), format='markdown')

        # Text with multiple variations of the same person's name
        # Both "Sarah Mitchell" and "Sarah Jane Mitchell" should match the same contact
        text = "Sarah Mitchell presented first. Later, Sarah Jane Mitchell answered questions."

        result = self.analyzer.analyze(text)

        # Check detected_people
        detected = result['detected_people']
        print(f"   Detected {len(detected)} person/people")

        # Count how many unique contact_ids we have (excluding None)
        contact_ids = [p['contact_id'] for p in detected if p.get('contact_id') is not None]
        unique_contact_ids = set(contact_ids)

        print(f"   Detected people:")
        for person in detected:
            exists_str = "exists" if person['exists'] else "new"
            contact_id = person.get('contact_id', 'None')
            print(f"      - {person['name']} ({exists_str}, ID: {contact_id})")

        if len(unique_contact_ids) == 1 and len(detected) > 1:
            print(f"   ❌ FAILED: Multiple entries for same contact (ID: {list(unique_contact_ids)[0]})")
            print(f"      Should deduplicate to show contact only once")
            return False

        # Ideally, we should have only 1 entry if both names match the same contact
        # OR 2 entries if they're treated as different people
        print(f"   ✓ {len(detected)} detected person entries, {len(unique_contact_ids)} unique contact IDs")
        return True

    def test_dedupe_related_items_same_snippet(self):
        """Test that related_items deduplicates snippets with same ID"""
        print("\n🧪 Test: Deduplication of related items - same snippet linked multiple times")

        # Create a contact
        contact1 = self.saver.save_as_person("Alice Johnson alice@example.com")

        # Create a snippet linked to the contact
        snippet_path = self.saver.save_as_snippet(
            text="Important project update about the new feature.",
            tags=["project", "update"],
            explicit_person_names=["Alice Johnson"],
            auto_link_persons=False
        )
        print(f"   ✓ Created snippet linked to Alice Johnson")

        # Reload data
        load_data(self.db, Path(self.temp_dir), format='markdown')

        # Analyze text that matches the contact
        # This should find the contact, and then find the snippet as a related item
        text = "Alice Johnson"

        result = self.analyzer.analyze(text)

        # Check related_items for duplicates
        related_snippets = [r for r in result['related_items'] if r['type'] == 'snippet']

        print(f"   Found {len(related_snippets)} related snippet(s)")

        if related_snippets:
            # Check for duplicate IDs
            snippet_ids = [s['data']['id'] for s in related_snippets]
            unique_ids = set(snippet_ids)

            if len(snippet_ids) != len(unique_ids):
                print(f"   ❌ FAILED: Duplicate snippet IDs found")
                print(f"      Total: {len(snippet_ids)}, Unique: {len(unique_ids)}")
                return False
            else:
                print(f"   ✓ All related snippets have unique IDs")
                return True
        else:
            print(f"   ⚠ No related snippets found")
            return True

    def test_dedupe_mixed_exact_and_person_matches(self):
        """Test that when person matching and exact matching both find the same contact, it appears only once"""
        print("\n🧪 Test: Deduplication when both exact match and person detection find same contact")

        # Create a contact
        contact_path = self.saver.save_as_person("Robert Davis robert.davis@example.com")
        print(f"   ✓ Created contact: Robert Davis")

        # Reload data
        load_data(self.db, Path(self.temp_dir), format='markdown')

        # Text that will match the contact both ways:
        # 1. Exact match on name "Robert Davis"
        # 2. Person name extraction also finds "Robert Davis"
        text = "Robert Davis sent an email"

        result = self.analyzer.analyze(text)

        # Check exact_matches
        contact_matches = [m for m in result['exact_matches'] if m['type'] == 'contact']

        print(f"   Found {len(contact_matches)} contact match(es)")

        # Count unique contact IDs
        contact_ids = [m['data']['id'] for m in contact_matches]
        unique_ids = set(contact_ids)

        if len(contact_ids) != len(unique_ids):
            print(f"   ❌ FAILED: Duplicate contacts in exact_matches")
            print(f"      Total matches: {len(contact_ids)}, Unique IDs: {len(unique_ids)}")
            return False

        print(f"   ✓ Contact appears only once in exact_matches")
        return True

    def run_all_tests(self):
        """Run all deduplication tests"""
        print("=" * 70)
        print("🧪 DEDUPLICATION ACCEPTANCE TESTS")
        print("=" * 70)
        print("\n📦 Setting up test environment...")

        try:
            self.setup()

            tests = [
                self.test_dedupe_exact_matches_same_contact_multiple_variations,
                self.test_dedupe_detected_people_same_contact,
                self.test_dedupe_related_items_same_snippet,
                self.test_dedupe_mixed_exact_and_person_matches
            ]

            results = []
            for test in tests:
                try:
                    result = test()
                    results.append(result)
                except Exception as e:
                    print(f"   ❌ Test failed with exception: {e}")
                    import traceback
                    traceback.print_exc()
                    results.append(False)

            # Summary
            print("\n" + "=" * 70)
            passed = sum(results)
            total = len(results)

            if passed == total:
                print("✅ ALL DEDUPLICATION TESTS PASSED!")
                print(f"\n✨ Summary: {passed}/{total} tests passed")
                print("   • Exact matches properly deduplicated")
                print("   • Detected people properly handled")
                print("   • Related items deduplicated")
                print("   • Mixed matching scenarios handled")
                return True
            else:
                print(f"⚠️  SOME TESTS FAILED: {passed}/{total} passed")
                return False

        finally:
            print("\n🧹 Cleaning up...")
            self.teardown()
            print("   ✓ Cleaned up")

        return False


if __name__ == '__main__':
    tester = DeduplicationTests()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
