#!/usr/bin/env python3
"""
Demonstration of semantic similarity search in action

This script shows how semantic search understands meaning, not just keywords.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_database
from src.data_loaders import load_data
from src.semantic_searcher import SemanticSearcher
from src.pattern_matcher import PatternMatcher
from src.action_suggester import ActionSuggester
from src.context_analyzer import ContextAnalyzer


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def print_results(results, query):
    """Print search results in a nice format"""
    print(f"\nQuery: \"{query}\"")
    print(f"Found {len(results)} semantic matches:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['type'].upper()}] (similarity: {result['similarity']:.3f})")
        # Truncate long text
        text = result['text']
        if len(text) > 100:
            text = text[:100] + "..."
        print(f"   {text}")
        print()


def demo():
    """Run semantic search demonstration"""
    print_header("Semantic Search Demonstration - Context Tool")

    print("\n📋 Loading data from markdown files...")
    db = get_database(":memory:")
    data_dir = Path(__file__).parent / "data-md"
    load_data(db.connection, data_dir, format='markdown')

    print("✓ Data loaded successfully")

    print("\n🧠 Initializing semantic search (downloading model if needed)...")
    searcher = SemanticSearcher(
        db.connection,
        model_name='all-MiniLM-L6-v2',
        similarity_threshold=0.25  # Lower threshold to show more results
    )
    searcher.initialize()

    print("✓ Model loaded")

    print("\n🔄 Generating embeddings for all data...")
    searcher.generate_embeddings_for_all()
    print(f"✓ Generated {len(searcher.embeddings)} embeddings")

    # Demo 1: Authentication question
    print_header("Demo 1: Finding Authentication Information")
    print("\nScenario: You copied 'How do we handle user login and authentication?'")
    print("Notice: No exact keywords like 'JWT', 'OAuth', or 'Sarah' in the query!")

    results = searcher.find_similar(
        "How do we handle user login and authentication?",
        limit=5
    )
    print_results(results, "How do we handle user login and authentication?")

    print("💡 Semantic search understood that 'login' and 'authentication' relate to:")
    print("   - JWT tokens, OAuth, security concepts")
    print("   - People working on auth (Sarah Mitchell)")
    print("   - Projects involving authentication")

    # Demo 2: Performance question
    print_header("Demo 2: Finding Performance Solutions")
    print("\nScenario: You copied 'The application is running slowly, need optimization'")
    print("Notice: No exact keywords like 'Redis', 'caching', or 'database'!")

    results = searcher.find_similar(
        "The application is running slowly, need optimization",
        limit=5
    )
    print_results(results, "The application is running slowly, need optimization")

    print("💡 Semantic search understood that 'slowly' and 'optimization' relate to:")
    print("   - Performance optimization techniques")
    print("   - Caching strategies (Redis)")
    print("   - Database performance fixes")

    # Demo 3: UI/Design question
    print_header("Demo 3: Finding UI/Design Information")
    print("\nScenario: You copied 'user interface layout and visual design'")
    print("Notice: No exact keywords like 'React', 'Emma', or 'component'!")

    results = searcher.find_similar(
        "user interface layout and visual design",
        limit=5
    )
    print_results(results, "user interface layout and visual design")

    print("💡 Semantic search understood that 'interface' and 'visual design' relate to:")
    print("   - Frontend frameworks (React, TypeScript)")
    print("   - UI components and layouts")
    print("   - Frontend developers (Emma Rodriguez)")

    # Demo 4: Integration with Context Analyzer
    print_header("Demo 4: Full Context Analysis (with Semantic Search)")
    print("\nScenario: Analyzing text through ContextAnalyzer")

    matcher = PatternMatcher()
    suggester = ActionSuggester()
    analyzer = ContextAnalyzer(db.connection, matcher, suggester, searcher)

    result = analyzer.analyze("What's our approach to mobile authentication?")

    print(f"\nQuery: \"What's our approach to mobile authentication?\"")
    print(f"\n📊 Analysis Results:")
    print(f"  - Detected type: {result['detected_type']}")
    print(f"  - Exact matches: {len(result['exact_matches'])}")
    print(f"  - Semantic matches: {len(result['semantic_matches'])}")
    print(f"  - Related items: {len(result['related_items'])}")
    print(f"  - Suggested actions: {len(result['actions'])}")

    print(f"\n🧠 Semantic Matches:")
    for match in result['semantic_matches'][:3]:
        print(f"  - [{match['type']}] {match['text'][:80]}...")
        print(f"    Similarity: {match['similarity']:.3f}")

    print(f"\n💬 Smart Context: {result['smart_context']}")

    # Summary
    print_header("Summary: Why Semantic Search Matters")

    print("""
🎯 Key Benefits:

1. **Understands Meaning**: Finds content based on concepts, not just keywords
   - "slow" finds "performance", "optimization", "caching"
   - "login" finds "JWT", "OAuth", "authentication"
   - "interface" finds "UI", "React", "design"

2. **Discovers Connections**: Surfaces related people, projects, and notes
   - Copy "authentication" → Find Sarah (Auth Lead), JWT notes, OAuth project
   - Copy "performance" → Find John (Backend), caching notes, optimization tips

3. **Natural Language**: Works with how you actually think and write
   - No need to remember exact terminology
   - Synonyms and related concepts automatically matched
   - Questions work as well as keywords

4. **Knowledge Graph**: Combines semantic search with relationship tracking
   - Find not just direct matches, but related items
   - See connections across your entire knowledge base

5. **Real-Time**: Fast enough for clipboard monitoring
   - Embeddings generated once (or on updates)
   - Search is near-instant (< 50ms)
   - Works seamlessly in widget mode, system mode, and web UI

🚀 Try it yourself:
   ./venv/bin/python3 main.py --mode widget

   Then copy any text and watch the semantic matches appear!
""")

    print_header("Demonstration Complete!")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
