#!/usr/bin/env python3
"""Test smart person name extraction and matching"""

from pathlib import Path
from src.database import get_database
from src.data_loaders import load_data
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer

# Initialize
db_obj = get_database(":memory:")
db = db_obj.connection

# Load markdown data
data_dir = Path("./data-md")
load_data(db, data_dir, format='markdown')

# Create analyzer
pattern_matcher = PatternMatcher()
action_suggester = ActionSuggester()
analyzer = ContextAnalyzer(
    db=db,
    pattern_matcher=pattern_matcher,
    action_suggester=action_suggester,
    semantic_searcher=None
)

print("=" * 70)
print("Testing Smart Person Name Extraction & Matching")
print("=" * 70)

# Test cases
test_cases = [
    "Discussed authentication with Emma Rodriguez today",
    "Meeting with Sarah Mitchell about OAuth implementation",
    "Emma and John Chen are working on the API",
    "Stefan Krona sent me the GitHub link",
    "Need to follow up with Sarah about the JWT tokens"
]

for test_text in test_cases:
    print(f"\n📝 Text: \"{test_text}\"")

    result = analyzer.analyze(test_text)

    exact_matches = result.get('exact_matches', [])

    if exact_matches:
        print(f"\n   ✓ Found {len(exact_matches)} contact(s):")
        for match in exact_matches:
            if match['type'] == 'contact':
                contact = match['data']
                score = match.get('match_score', 'N/A')
                reason = match.get('match_reason', '')
                print(f"      - {contact['name']} (score: {score}) - {reason}")
    else:
        print("   ✗ No contacts found")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
