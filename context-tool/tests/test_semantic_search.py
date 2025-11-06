"""Semantic similarity search tests for Context Tool

Tests the semantic search functionality including:
- Embedding generation
- Similarity calculations
- Integration with context analyzer
- Real-world use cases with clipboard text
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database
from src.semantic_searcher import SemanticSearcher
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


# Test data: realistic context notes
TEST_SNIPPETS = [
    {
        "text": "Discussed authentication implementation with Sarah. We decided to use JWT tokens with RS256 signing for the API. Need to implement refresh token rotation and store tokens in httpOnly cookies.",
        "tags": "auth, security, api",
        "metadata": '{"linked_projects": ["Context Tool"]}'
    },
    {
        "text": "Meeting notes from OAuth integration discussion. Team agreed on using OAuth 2.0 with PKCE flow for mobile apps. Sarah will lead the implementation.",
        "tags": "oauth, mobile, security",
        "metadata": '{}'
    },
    {
        "text": "Bug fix for database connection pooling. Fixed thread safety issues in SQLite connections by adding check_same_thread=False for read-only operations.",
        "tags": "bug, database, threading",
        "metadata": '{}'
    },
    {
        "text": "Performance optimization notes: implemented caching layer using Redis. Reduced API response time from 200ms to 50ms. Need to monitor memory usage.",
        "tags": "performance, caching, redis",
        "metadata": '{}'
    },
    {
        "text": "Design review for new dashboard UI. Using React with TypeScript. Implementing dark mode toggle and responsive layout for mobile devices.",
        "tags": "ui, react, design",
        "metadata": '{}'
    }
]

TEST_CONTACTS = [
    {
        "name": "Sarah Mitchell",
        "email": "sarah.m@company.com",
        "role": "Auth Team Lead",
        "context": "Leading authentication and security features. Expert in OAuth, JWT, and mobile auth.",
        "tags": "teammate, auth, security"
    },
    {
        "name": "John Chen",
        "email": "john.c@company.com",
        "role": "Backend Developer",
        "context": "Working on database optimization and caching. Recently fixed threading issues in SQLite.",
        "tags": "teammate, database, backend"
    },
    {
        "name": "Emma Rodriguez",
        "email": "emma.r@company.com",
        "role": "Frontend Lead",
        "context": "Leading UI/UX development. Specializes in React, TypeScript, and responsive design.",
        "tags": "teammate, frontend, ui"
    }
]

TEST_PROJECTS = [
    {
        "name": "Context Tool",
        "status": "active",
        "description": "Smart context notes system with semantic search, knowledge graph, and clipboard monitoring.",
        "tags": "internal, productivity",
        "metadata": '{"team_lead": "Sarah Mitchell"}'
    },
    {
        "name": "Mobile Auth Redesign",
        "status": "planning",
        "description": "Implementing OAuth 2.0 with PKCE for mobile applications. Includes token refresh and biometric authentication.",
        "tags": "security, mobile",
        "metadata": '{"team_lead": "Sarah Mitchell"}'
    }
]


def setup_test_database():
    """Create test database with sample data"""
    print("Setting up test database...")

    db = get_database(":memory:")

    # Insert test contacts
    for contact in TEST_CONTACTS:
        db.connection.execute("""
            INSERT INTO contacts (name, email, role, context, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            contact['name'],
            contact['email'],
            contact['role'],
            contact['context'],
            contact['tags'],
            '{}'
        ))

    # Insert test snippets
    for snippet in TEST_SNIPPETS:
        db.connection.execute("""
            INSERT INTO snippets (text, tags, metadata, saved_date, source)
            VALUES (?, ?, ?, datetime('now'), 'test')
        """, (
            snippet['text'],
            snippet['tags'],
            snippet['metadata']
        ))

    # Insert test projects
    for project in TEST_PROJECTS:
        db.connection.execute("""
            INSERT INTO projects (name, status, description, tags, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project['name'],
            project['status'],
            project['description'],
            project['tags'],
            project['metadata']
        ))

    db.connection.commit()
    print(f"  ✓ Inserted {len(TEST_CONTACTS)} contacts")
    print(f"  ✓ Inserted {len(TEST_SNIPPETS)} snippets")
    print(f"  ✓ Inserted {len(TEST_PROJECTS)} projects")

    return db


def test_semantic_searcher_initialization():
    """Test semantic searcher initialization"""
    print("\nTesting semantic searcher initialization...")

    db = get_database(":memory:")
    searcher = SemanticSearcher(
        db.connection,
        model_name='all-MiniLM-L6-v2',
        similarity_threshold=0.3
    )

    assert searcher.model is None, "Model should not be loaded until initialize() is called"
    assert searcher.similarity_threshold == 0.3

    print("  ✓ Lazy loading works")

    # Initialize the model
    searcher.initialize()

    assert searcher.model is not None, "Model should be loaded after initialize()"
    print("  ✓ Model loaded successfully")

    print("✓ Semantic searcher initialization passed")
    return searcher


def test_embedding_generation():
    """Test embedding generation for all entities"""
    print("\nTesting embedding generation...")

    db = setup_test_database()
    searcher = SemanticSearcher(db.connection, similarity_threshold=0.3)
    searcher.initialize()

    # Generate embeddings
    searcher.generate_embeddings_for_all()

    # Check embeddings were created
    cursor = db.connection.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]

    expected_count = len(TEST_CONTACTS) + len(TEST_SNIPPETS) + len(TEST_PROJECTS)
    assert embedding_count == expected_count, f"Expected {expected_count} embeddings, got {embedding_count}"

    print(f"  ✓ Generated {embedding_count} embeddings")

    # Verify embedding structure
    cursor = db.connection.execute("SELECT * FROM embeddings LIMIT 1")
    row = cursor.fetchone()

    assert row['entity_type'] in ['contact', 'snippet', 'project']
    assert row['entity_id'] > 0
    assert row['embedding'] is not None
    assert row['text'] is not None

    # Verify embedding can be decoded
    embedding_bytes = row['embedding']
    embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
    assert len(embedding_array) == 384, "all-MiniLM-L6-v2 produces 384-dimensional embeddings"

    print(f"  ✓ Embeddings are 384-dimensional vectors")
    print(f"  ✓ Embeddings stored correctly in database")

    print("✓ Embedding generation passed")
    return db, searcher


def test_similarity_search_basic():
    """Test basic similarity search functionality"""
    print("\nTesting basic similarity search...")

    db, searcher = test_embedding_generation()

    # Test 1: Search for authentication-related content
    results = searcher.find_similar("How do we handle user authentication?", limit=3)

    assert len(results) > 0, "Should find authentication-related content"

    # Should find auth-related snippets and Sarah (auth lead)
    auth_related = [r for r in results if 'auth' in r['text'].lower() or 'jwt' in r['text'].lower()]
    assert len(auth_related) > 0, "Should find auth-related results"

    print(f"  ✓ Found {len(results)} results for 'user authentication'")
    for r in results[:3]:
        print(f"    - {r['type']}: {r['text'][:60]}... (score: {r['similarity']:.3f})")

    # Test 2: Search for database-related content
    results = searcher.find_similar("database performance issues", limit=3)

    db_related = [r for r in results if 'database' in r['text'].lower() or 'sqlite' in r['text'].lower()]
    assert len(db_related) > 0, "Should find database-related results"

    print(f"  ✓ Found {len(results)} results for 'database performance'")

    # Test 3: Search for UI/frontend content
    results = searcher.find_similar("user interface design", limit=3)

    ui_related = [r for r in results if 'ui' in r['text'].lower() or 'react' in r['text'].lower()]
    assert len(ui_related) > 0, "Should find UI-related results"

    print(f"  ✓ Found {len(results)} results for 'user interface'")

    print("✓ Basic similarity search passed")


def test_similarity_threshold():
    """Test similarity threshold filtering"""
    print("\nTesting similarity threshold...")

    db, searcher = test_embedding_generation()

    # Set low threshold
    searcher.similarity_threshold = 0.1
    results_low = searcher.find_similar("authentication", limit=10)

    # Set high threshold
    searcher.similarity_threshold = 0.6
    results_high = searcher.find_similar("authentication", limit=10)

    assert len(results_low) >= len(results_high), "Lower threshold should return more results"

    # All results should meet threshold
    for r in results_high:
        assert r['similarity'] >= 0.6, f"Result similarity {r['similarity']} below threshold 0.6"

    print(f"  ✓ Low threshold (0.1): {len(results_low)} results")
    print(f"  ✓ High threshold (0.6): {len(results_high)} results")
    print(f"  ✓ Threshold filtering working correctly")

    print("✓ Similarity threshold test passed")


def test_find_similar_to_entity():
    """Test finding items similar to a specific entity"""
    print("\nTesting find similar to entity...")

    db, searcher = test_embedding_generation()

    # Find the first snippet (about JWT authentication)
    cursor = db.connection.execute("SELECT id FROM snippets WHERE text LIKE '%JWT%' LIMIT 1")
    jwt_snippet_id = cursor.fetchone()[0]

    # Find similar items
    results = searcher.find_similar_to_entity('snippet', jwt_snippet_id, limit=5)

    assert len(results) > 0, "Should find items similar to JWT snippet"

    # Should find auth-related content (OAuth snippet, Sarah, etc.)
    print(f"  ✓ Found {len(results)} items similar to JWT snippet:")
    for r in results[:3]:
        print(f"    - {r['type']}: {r['text'][:60]}... (score: {r['similarity']:.3f})")

    # The results should not include the original snippet itself
    original_in_results = any(r['type'] == 'snippet' and r['id'] == jwt_snippet_id for r in results)
    assert not original_in_results, "Results should not include the query entity itself"

    print(f"  ✓ Original entity excluded from results")

    print("✓ Find similar to entity passed")


def test_integration_with_analyzer():
    """Test semantic search integration with context analyzer"""
    print("\nTesting integration with context analyzer...")

    db, searcher = test_embedding_generation()

    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, searcher)

    # Analyze text that should trigger semantic matches
    result = analyzer.analyze("How should we implement token-based authentication?")

    # Check semantic matches are included
    assert 'semantic_matches' in result
    assert len(result['semantic_matches']) > 0, "Should find semantic matches"

    print(f"  ✓ Context analyzer found {len(result['semantic_matches'])} semantic matches")

    # Verify results are relevant
    for match in result['semantic_matches'][:3]:
        print(f"    - {match['type']}: {match['text'][:60]}... (score: {match['similarity']:.3f})")

    # Check the full analysis result structure
    assert result['selected_text'] == "How should we implement token-based authentication?"
    assert 'exact_matches' in result
    assert 'related_items' in result
    assert 'smart_context' in result

    print("  ✓ Full analysis result structure correct")

    print("✓ Integration with analyzer passed")


def test_clipboard_simulation():
    """Test real-world clipboard scenarios with semantic search"""
    print("\nTesting clipboard simulation scenarios...")

    db, searcher = test_embedding_generation()

    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, searcher)

    # Scenario 1: User copies a question about security
    clipboard_text = "What's our approach to securing API tokens?"
    result = analyzer.analyze(clipboard_text)

    assert len(result['semantic_matches']) > 0, "Should find security-related content"

    # Should find JWT snippet and Sarah (auth lead)
    auth_matches = [m for m in result['semantic_matches']
                    if 'auth' in m['text'].lower() or 'token' in m['text'].lower()]
    assert len(auth_matches) > 0, "Should find token/auth related matches"

    print(f"  ✓ Scenario 1: Security question")
    print(f"    Found {len(auth_matches)} relevant matches")

    # Scenario 2: User copies text about performance
    clipboard_text = "The API is slow, we need to optimize response times"
    result = analyzer.analyze(clipboard_text)

    perf_matches = [m for m in result['semantic_matches']
                    if 'performance' in m['text'].lower() or 'caching' in m['text'].lower()]

    print(f"  ✓ Scenario 2: Performance issue")
    print(f"    Found {len(perf_matches)} performance-related matches")

    # Scenario 3: User copies a name
    clipboard_text = "Sarah"
    result = analyzer.analyze(clipboard_text)

    # Should find Sarah via exact match AND semantic matches to her projects
    sarah_semantic = [m for m in result['semantic_matches']
                      if 'sarah' in m['text'].lower()]

    print(f"  ✓ Scenario 3: Person name")
    print(f"    Found semantic matches: {len(result['semantic_matches'])}")

    # Scenario 4: User copies technical jargon
    clipboard_text = "React hooks and state management"
    result = analyzer.analyze(clipboard_text)

    # Should find UI/React related content
    react_matches = [m for m in result['semantic_matches']
                     if 'react' in m['text'].lower() or 'ui' in m['text'].lower()]

    print(f"  ✓ Scenario 4: Technical jargon")
    print(f"    Found {len(react_matches)} React/UI matches")

    print("✓ Clipboard simulation passed")


def test_semantic_search_quality():
    """Test the quality of semantic search results"""
    print("\nTesting semantic search quality...")

    db, searcher = test_embedding_generation()

    # Test: Semantic understanding (synonyms and concepts)
    test_cases = [
        {
            "query": "password security",
            "should_find": ["auth", "jwt", "oauth", "token"],
            "description": "Should understand password relates to authentication"
        },
        {
            "query": "speed improvements",
            "should_find": ["performance", "optimization", "caching"],
            "description": "Should understand speed relates to performance"
        },
        {
            "query": "visual design",
            "should_find": ["ui", "dashboard", "react"],
            "description": "Should understand visual relates to UI"
        }
    ]

    for test in test_cases:
        results = searcher.find_similar(test['query'], limit=5)

        # Check if results contain expected terms
        found_terms = []
        for term in test['should_find']:
            if any(term.lower() in r['text'].lower() for r in results):
                found_terms.append(term)

        coverage = len(found_terms) / len(test['should_find'])

        print(f"  ✓ '{test['query']}': {len(found_terms)}/{len(test['should_find'])} expected terms found")
        print(f"    {test['description']}")

        # At least 50% of expected terms should be found
        assert coverage >= 0.5, f"Only {coverage*100:.0f}% of expected terms found for '{test['query']}'"

    print("✓ Semantic search quality test passed")


def main():
    """Run all semantic search tests"""
    print("=" * 70)
    print("Context Tool - Semantic Similarity Search Tests")
    print("=" * 70)

    try:
        # Test 1: Initialization
        test_semantic_searcher_initialization()

        # Test 2: Embedding generation
        test_embedding_generation()

        # Test 3: Basic similarity search
        test_similarity_search_basic()

        # Test 4: Threshold filtering
        test_similarity_threshold()

        # Test 5: Similar to entity
        test_find_similar_to_entity()

        # Test 6: Integration with analyzer
        test_integration_with_analyzer()

        # Test 7: Clipboard simulation
        test_clipboard_simulation()

        # Test 8: Search quality
        test_semantic_search_quality()

        print("\n" + "=" * 70)
        print("✅ All semantic search tests passed!")
        print("=" * 70)
        print("\nSemantic search is working correctly and ready for use.")
        print("The feature provides intelligent matching based on meaning,")
        print("not just keywords, making the context tool much more powerful.")
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
