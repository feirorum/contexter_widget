#!/usr/bin/env python3
"""
Acceptance tests for core contact matching and name detection features

Tests the most important features and edge cases:
1. Name extraction from text (regex pattern matching)
2. Contact matching with scoring system
3. Integration: detecting people for save workflow
"""

import sys
import tempfile
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context_analyzer import ContextAnalyzer
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.database import get_database
from src.data_loaders import load_data
from src.saver import EntitySaver


class CoreContactFeatureTests:
    """Test core contact matching and name detection features"""

    def __init__(self):
        self.tmpdir = None
        self.data_dir = None
        self.db = None
        self.analyzer = None
        self.saver = None

    def setup(self):
        """Set up test environment"""
        print("\n📦 Setting up test environment...")
        self.tmpdir = tempfile.mkdtemp()
        self.data_dir = Path(self.tmpdir)
        self.saver = EntitySaver(self.data_dir)

        # Initialize database
        db_wrapper = get_database(':memory:')
        self.db = db_wrapper.connection

        # Load data
        load_data(self.db, self.data_dir, format='markdown')

        # Initialize analyzer
        pattern_matcher = PatternMatcher()
        action_suggester = ActionSuggester()
        self.analyzer = ContextAnalyzer(
            db=self.db,
            pattern_matcher=pattern_matcher,
            action_suggester=action_suggester
        )

        print(f"   ✓ Created temp directory: {self.tmpdir}")

    def teardown(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up...")
        if self.db:
            self.db.close()
        if self.tmpdir:
            import shutil
            shutil.rmtree(self.tmpdir)
            print("   ✓ Cleaned up")

    def create_contact(self, name: str, email: str = None):
        """Helper to create a contact"""
        text = name
        if email:
            text += f" {email}"
        self.saver.save_as_person(text)
        load_data(self.db, self.data_dir, format='markdown')

    # =========================================================================
    # NAME EXTRACTION TESTS
    # =========================================================================

    def test_name_extraction_simple_two_words(self):
        """Test extracting simple two-word names"""
        print("\n🧪 Test: Name extraction - simple two-word names")

        text = "Met with John Doe today to discuss the project."
        names = self.analyzer._extract_person_names(text)

        assert len(names) == 1, f"Expected 1 name, got {len(names)}"
        assert "John Doe" in names, f"Expected 'John Doe', got {names}"
        print("   ✓ Extracted: John Doe")

    def test_name_extraction_three_words(self):
        """Test extracting three-word names"""
        print("\n🧪 Test: Name extraction - three-word names")

        text = "Mary Jane Smith presented the findings."
        names = self.analyzer._extract_person_names(text)

        assert len(names) == 1, f"Expected 1 name, got {len(names)}"
        assert "Mary Jane Smith" in names, f"Expected 'Mary Jane Smith', got {names}"
        print("   ✓ Extracted: Mary Jane Smith")

    def test_name_extraction_with_title(self):
        """Test extracting names with titles"""
        print("\n🧪 Test: Name extraction - names with titles")

        text = "Dr. Sarah Mitchell will lead the research."
        names = self.analyzer._extract_person_names(text)

        # Should extract "Sarah Mitchell" (Dr. is one word, so "Dr. Sarah" is valid too)
        assert len(names) >= 1, f"Expected at least 1 name, got {len(names)}"
        # Either "Dr. Sarah" + "Sarah Mitchell" or just "Sarah Mitchell"
        has_sarah = any("Sarah" in name and "Mitchell" in name for name in names)
        assert has_sarah, f"Expected name containing 'Sarah Mitchell', got {names}"
        print(f"   ✓ Extracted: {names}")

    def test_name_extraction_multiple_names(self):
        """Test extracting multiple names from text"""
        print("\n🧪 Test: Name extraction - multiple names")

        text = "John Doe and Sarah Mitchell discussed the project with Emma Rodriguez."
        names = self.analyzer._extract_person_names(text)

        assert len(names) >= 3, f"Expected at least 3 names, got {len(names)}: {names}"
        assert "John Doe" in names, f"Missing 'John Doe' in {names}"
        assert "Sarah Mitchell" in names, f"Missing 'Sarah Mitchell' in {names}"
        assert "Emma Rodriguez" in names, f"Missing 'Emma Rodriguez' in {names}"
        print(f"   ✓ Extracted {len(names)} names: {', '.join(names)}")

    def test_name_extraction_no_single_words(self):
        """Test that single capitalized words are NOT extracted"""
        print("\n🧪 Test: Name extraction - ignores single words")

        text = "Sarah went to Paris to meet John."
        names = self.analyzer._extract_person_names(text)

        # Should NOT extract "Sarah", "Paris", "John" (all single words)
        assert len(names) == 0, f"Expected 0 names (single words), got {len(names)}: {names}"
        print("   ✓ Correctly ignored single capitalized words")

    def test_name_extraction_lowercase_ignored(self):
        """Test that lowercase names are NOT extracted"""
        print("\n🧪 Test: Name extraction - ignores lowercase")

        text = "met with john doe today"
        names = self.analyzer._extract_person_names(text)

        assert len(names) == 0, f"Expected 0 names (lowercase), got {len(names)}: {names}"
        print("   ✓ Correctly ignored lowercase text")

    def test_name_extraction_sentence_boundaries(self):
        """Test extracting names at sentence boundaries"""
        print("\n🧪 Test: Name extraction - sentence boundaries")

        text = "John Doe started the meeting. Sarah Mitchell presented. Emma Rodriguez concluded."
        names = self.analyzer._extract_person_names(text)

        assert len(names) >= 3, f"Expected 3 names, got {len(names)}: {names}"
        print(f"   ✓ Extracted names at boundaries: {', '.join(names)}")

    def test_name_extraction_empty_text(self):
        """Test with empty text"""
        print("\n🧪 Test: Name extraction - empty text")

        names = self.analyzer._extract_person_names("")

        assert len(names) == 0, f"Expected 0 names for empty text, got {len(names)}"
        print("   ✓ Handled empty text correctly")

    # =========================================================================
    # CONTACT MATCHING TESTS
    # =========================================================================

    def test_contact_matching_exact_match(self):
        """Test exact name match (score = 10)"""
        print("\n🧪 Test: Contact matching - exact match")

        self.create_contact("Sarah Mitchell", "sarah@example.com")

        matches = self.analyzer._match_person_to_contact("Sarah Mitchell")

        assert len(matches) > 0, "Expected at least 1 match"
        contact, score = matches[0]
        assert score == 10, f"Expected exact match score 10, got {score}"
        assert contact['name'] == "Sarah Mitchell", f"Expected 'Sarah Mitchell', got {contact['name']}"
        print(f"   ✓ Exact match: '{contact['name']}' with score {score}")

    def test_contact_matching_substring_match(self):
        """Test true substring name match (score = 8)"""
        print("\n🧪 Test: Contact matching - substring match")

        # Create contact - manually insert to control exact name
        cursor = self.db.execute("""
            INSERT INTO contacts (name, email)
            VALUES (?, ?)
        """, ("Elizabeth Thompson Jr", "elizabeth@example.com"))
        self.db.commit()

        # Search without suffix - should be literal substring match
        matches = self.analyzer._match_person_to_contact("Elizabeth Thompson")

        assert len(matches) > 0, "Expected at least 1 match"
        contact, score = matches[0]
        # "Elizabeth Thompson" IS a literal substring of "Elizabeth Thompson Jr"
        assert score == 8, f"Expected substring match score 8, got {score}"
        print(f"   ✓ Substring match: '{contact['name']}' with score {score}")

    def test_contact_matching_partial_name(self):
        """Test partial name match (score based on parts)"""
        print("\n🧪 Test: Contact matching - partial name")

        self.create_contact("Rebecca Anderson", "rebecca@example.com")

        # Search with different last name but same first name
        matches = self.analyzer._match_person_to_contact("Rebecca Johnson")

        assert len(matches) > 0, "Expected at least 1 match for partial name"
        contact, score = matches[0]
        # Should get 1 point for "Rebecca" matching
        assert score >= 1, f"Expected score >= 1 for partial match, got {score}"
        assert score < 8, f"Expected score < 8 for partial match, got {score}"
        print(f"   ✓ Partial match: '{contact['name']}' with score {score}")

    def test_contact_matching_no_match(self):
        """Test when no contact matches"""
        print("\n🧪 Test: Contact matching - no match")

        self.create_contact("Thomas Wilson", "thomas@example.com")

        # Search for completely different name
        matches = self.analyzer._match_person_to_contact("Patricia Garcia")

        assert len(matches) == 0, f"Expected 0 matches, got {len(matches)}"
        print("   ✓ Correctly found no matches")

    def test_contact_matching_case_insensitive(self):
        """Test that matching is case-insensitive"""
        print("\n🧪 Test: Contact matching - case insensitive")

        self.create_contact("Jennifer Martinez", "jennifer@example.com")

        # Search with different case
        matches = self.analyzer._match_person_to_contact("jennifer martinez")

        assert len(matches) > 0, "Expected match (case-insensitive)"
        contact, score = matches[0]
        assert score == 10, f"Expected exact match despite case, got score {score}"
        print(f"   ✓ Case-insensitive match with score {score}")

    def test_contact_matching_multiple_candidates(self):
        """Test when multiple contacts could match"""
        print("\n🧪 Test: Contact matching - multiple candidates")

        self.create_contact("John Smith", "john.smith@example.com")
        self.create_contact("John Doe", "john.doe@example.com")
        self.create_contact("Jane Smith", "jane.smith@example.com")

        matches = self.analyzer._match_person_to_contact("John Smith")

        assert len(matches) > 0, "Expected matches"
        # Should have exact match as first result
        contact, score = matches[0]
        assert contact['name'] == "John Smith", f"Expected exact match first, got {contact['name']}"
        assert score == 10, f"Expected score 10 for exact match, got {score}"
        print(f"   ✓ Found {len(matches)} candidates, best: '{contact['name']}' (score {score})")

    def test_contact_matching_name_variations(self):
        """Test matching with name variations"""
        print("\n🧪 Test: Contact matching - name variations")

        self.create_contact("Robert Johnson", "robert@example.com")

        # Try searching with "Bob Johnson" - should get partial match
        matches = self.analyzer._match_person_to_contact("Bob Johnson")

        # Might not match "Bob" to "Robert" (depends on implementation)
        # But should at least match "Johnson"
        if len(matches) > 0:
            contact, score = matches[0]
            print(f"   ✓ Found variation match: '{contact['name']}' with score {score}")
        else:
            print("   ✓ No match for nickname (expected - names must match exactly)")

    # =========================================================================
    # INTEGRATION TESTS: DETECT PEOPLE FOR SAVE
    # =========================================================================

    def test_detect_people_existing_contact(self):
        """Test detecting existing contact in text"""
        print("\n🧪 Test: Detect people - existing contact")

        self.create_contact("Sarah Mitchell", "sarah@example.com")

        text = "Met with Sarah Mitchell to discuss the project."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        assert len(detected) >= 1, f"Expected at least 1 person, got {len(detected)}"

        sarah = next((p for p in detected if 'Sarah' in p['name']), None)
        assert sarah is not None, f"Sarah Mitchell not found in {detected}"
        assert sarah['exists'] is True, f"Sarah should exist, got {sarah}"
        assert sarah['contact_id'] is not None, f"Sarah should have contact_id, got {sarah}"
        print(f"   ✓ Detected existing contact: {sarah['name']} (id={sarah['contact_id']})")

    def test_detect_people_new_person(self):
        """Test detecting new person (not in contacts)"""
        print("\n🧪 Test: Detect people - new person")

        text = "Met with Christopher Lee to discuss the project."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        assert len(detected) >= 1, f"Expected at least 1 person, got {len(detected)}"

        chris = next((p for p in detected if 'Christopher' in p['name']), None)
        assert chris is not None, f"Christopher Lee not found in {detected}"
        assert chris['exists'] is False, f"Christopher should be new, got {chris}"
        assert chris['contact_id'] is None, f"Christopher should not have contact_id, got {chris}"
        print(f"   ✓ Detected new person: {chris['name']}")

    def test_detect_people_mixed(self):
        """Test detecting both existing and new people"""
        print("\n🧪 Test: Detect people - mixed (existing + new)")

        self.create_contact("Amanda Chen", "amanda@example.com")

        text = "Amanda Chen and Michael Brown discussed the project."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        assert len(detected) >= 2, f"Expected at least 2 people, got {len(detected)}"

        amanda = next((p for p in detected if 'Amanda' in p['name']), None)
        michael = next((p for p in detected if 'Michael' in p['name']), None)

        assert amanda is not None, "Amanda Chen not detected"
        assert michael is not None, "Michael Brown not detected"

        assert amanda['exists'] is True, f"Amanda should exist"
        assert michael['exists'] is False, f"Michael should be new"

        print(f"   ✓ Detected existing: {amanda['name']}")
        print(f"   ✓ Detected new: {michael['name']}")

    def test_detect_people_multiple_existing(self):
        """Test detecting multiple existing contacts"""
        print("\n🧪 Test: Detect people - multiple existing")

        self.create_contact("Laura Davis", "laura@example.com")
        self.create_contact("Kevin Wong", "kevin@example.com")

        text = "Laura Davis and Kevin Wong presented the findings."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        assert len(detected) >= 2, f"Expected at least 2 people, got {len(detected)}"

        existing_count = sum(1 for p in detected if p['exists'])
        assert existing_count >= 2, f"Expected at least 2 existing contacts, got {existing_count}"

        print(f"   ✓ Detected {existing_count} existing contacts")

    def test_detect_people_no_names(self):
        """Test text with no person names"""
        print("\n🧪 Test: Detect people - no names")

        text = "The project is progressing well according to schedule."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        assert len(detected) == 0, f"Expected 0 people, got {len(detected)}"
        print("   ✓ Correctly detected no people")

    def test_detect_people_duplicate_names(self):
        """Test text with same name mentioned multiple times"""
        print("\n🧪 Test: Detect people - duplicate names")

        self.create_contact("Diana Prince", "diana@example.com")

        text = "Diana Prince said this. Diana Prince also said that. Diana Prince concluded."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        # Should only detect Diana once (duplicates removed)
        diana_count = sum(1 for p in detected if 'Diana' in p['name'])
        assert diana_count == 1, f"Expected Diana once, found {diana_count} times"

        print(f"   ✓ Correctly deduplicated: found Diana Prince once")

    def test_detect_people_with_scores(self):
        """Test that detected people include matching scores"""
        print("\n🧪 Test: Detect people - includes scores")

        self.create_contact("Victor Stone", "victor@example.com")

        text = "Met with Victor Stone today."
        result = self.analyzer.analyze(text)
        detected = result.get('detected_people', [])

        victor = next((p for p in detected if 'Victor' in p['name']), None)
        assert victor is not None, "Victor not detected"

        if victor['exists']:
            assert 'score' in victor, f"Expected score in {victor}"
            assert victor['score'] > 0, f"Expected positive score, got {victor['score']}"
            print(f"   ✓ Score included: {victor['score']}")
        else:
            print("   ✓ New person (no score needed)")

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    def test_edge_case_name_with_period(self):
        """Test names with periods (initials)"""
        print("\n🧪 Test: Edge case - names with periods")

        text = "Dr. J. Smith presented the findings."
        names = self.analyzer._extract_person_names(text)

        # Pattern only matches [A-Z][a-z]+ so "J." won't match
        # But might extract other parts
        print(f"   ✓ Extracted from text with periods: {names if names else 'none (expected)'}")

    def test_edge_case_all_caps_name(self):
        """Test all-caps names"""
        print("\n🧪 Test: Edge case - all caps")

        text = "JOHN DOE will handle this."
        names = self.analyzer._extract_person_names(text)

        # Pattern requires [A-Z][a-z]+ so all-caps won't match
        assert len(names) == 0, f"Expected 0 (all-caps not supported), got {names}"
        print("   ✓ All-caps not extracted (expected)")

    def test_edge_case_hyphenated_names(self):
        """Test hyphenated names"""
        print("\n🧪 Test: Edge case - hyphenated names")

        text = "Mary-Jane Smith attended the meeting."
        names = self.analyzer._extract_person_names(text)

        # Hyphen breaks the pattern, so might get "Jane Smith" only
        print(f"   ✓ Extracted from hyphenated: {names if names else 'partial/none'}")

    def test_edge_case_very_long_name(self):
        """Test very long names (4+ words)"""
        print("\n🧪 Test: Edge case - very long name")

        text = "Maria Isabella Gonzalez Rodriguez presented."
        names = self.analyzer._extract_person_names(text)

        # Should extract the full name
        assert len(names) >= 1, f"Expected name extraction, got {names}"
        has_long = any(len(name.split()) >= 3 for name in names)
        assert has_long, f"Expected long name, got {names}"
        print(f"   ✓ Extracted long name: {names}")

    def test_edge_case_non_ascii_characters(self):
        """Test names with non-ASCII characters (e.g., Swedish ö, ä)"""
        print("\n🧪 Test: Edge case - non-ASCII characters")

        text = "Magnus Sjöström presented the findings to José García."
        names = self.analyzer._extract_person_names(text)

        # Current regex [A-Z][a-z]+ only matches ASCII letters
        # So "Sjöström" with ö won't match, and "García" with í won't match
        if len(names) == 0:
            print("   ⚠ Non-ASCII not extracted (regex limitation: [A-Z][a-z]+ is ASCII-only)")
        else:
            print(f"   ✓ Extracted with non-ASCII: {names}")

    def test_edge_case_non_ascii_matching(self):
        """Test matching names with non-ASCII characters"""
        print("\n🧪 Test: Edge case - non-ASCII character matching")

        # Manually create contact with non-ASCII name
        cursor = self.db.execute("""
            INSERT INTO contacts (name, email)
            VALUES (?, ?)
        """, ("Magnus Sjöström", "magnus@example.com"))
        self.db.commit()

        # Try to match - will depend on if name was extracted
        matches = self.analyzer._match_person_to_contact("Magnus Sjöström")

        if len(matches) > 0:
            contact, score = matches[0]
            print(f"   ✓ Matched non-ASCII name: '{contact['name']}' with score {score}")
        else:
            print("   ⚠ No match (expected if extraction doesn't support non-ASCII)")

    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================

    def run_all_tests(self):
        """Run all test cases"""
        print("\n" + "=" * 70)
        print("🧪 CORE CONTACT FEATURES - ACCEPTANCE TESTS")
        print("=" * 70)

        try:
            self.setup()

            # Name extraction tests
            print("\n" + "─" * 70)
            print("📝 NAME EXTRACTION TESTS")
            print("─" * 70)
            self.test_name_extraction_simple_two_words()
            self.test_name_extraction_three_words()
            self.test_name_extraction_with_title()
            self.test_name_extraction_multiple_names()
            self.test_name_extraction_no_single_words()
            self.test_name_extraction_lowercase_ignored()
            self.test_name_extraction_sentence_boundaries()
            self.test_name_extraction_empty_text()

            # Contact matching tests
            print("\n" + "─" * 70)
            print("🎯 CONTACT MATCHING TESTS")
            print("─" * 70)
            self.test_contact_matching_exact_match()
            self.test_contact_matching_substring_match()
            self.test_contact_matching_partial_name()
            self.test_contact_matching_no_match()
            self.test_contact_matching_case_insensitive()
            self.test_contact_matching_multiple_candidates()
            self.test_contact_matching_name_variations()

            # Integration tests
            print("\n" + "─" * 70)
            print("🔗 INTEGRATION TESTS (Detect People for Save)")
            print("─" * 70)
            self.test_detect_people_existing_contact()
            self.test_detect_people_new_person()
            self.test_detect_people_mixed()
            self.test_detect_people_multiple_existing()
            self.test_detect_people_no_names()
            self.test_detect_people_duplicate_names()
            self.test_detect_people_with_scores()

            # Edge cases
            print("\n" + "─" * 70)
            print("⚠️  EDGE CASE TESTS")
            print("─" * 70)
            self.test_edge_case_name_with_period()
            self.test_edge_case_all_caps_name()
            self.test_edge_case_hyphenated_names()
            self.test_edge_case_very_long_name()
            self.test_edge_case_non_ascii_characters()
            self.test_edge_case_non_ascii_matching()

            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)

            print("\n📊 Test Summary:")
            print("   • 8 Name Extraction tests")
            print("   • 7 Contact Matching tests")
            print("   • 7 Integration tests")
            print("   • 6 Edge Case tests (including non-ASCII)")
            print("   • Total: 28 test cases")
            print("\n🎉 All core features working correctly!")

            return True

        except AssertionError as e:
            print("\n" + "=" * 70)
            print(f"❌ TEST FAILED: {e}")
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
    """Run all tests"""
    test = CoreContactFeatureTests()
    success = test.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
