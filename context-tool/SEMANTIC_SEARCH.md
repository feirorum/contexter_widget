# Semantic Search Feature

The Context Tool includes powerful semantic similarity search using sentence transformers and embeddings. This allows the tool to find contextually related notes even when they don't share exact keywords.

## What is Semantic Search?

Semantic search understands the **meaning** of your text, not just keywords:

- **Traditional search**: Looks for exact word matches (e.g., "JWT" finds only documents with "JWT")
- **Semantic search**: Understands concepts (e.g., "authentication" finds JWT, OAuth, login, tokens, etc.)

## How It Works

1. **Embeddings Generation**: When you load data, the tool converts each snippet, contact, and project into a 384-dimensional vector (embedding) that captures its meaning
2. **Similarity Calculation**: When you copy text, the tool:
   - Converts your text to an embedding
   - Calculates cosine similarity with all stored embeddings
   - Returns the most semantically similar items
3. **Smart Matching**: Results are ranked by similarity score (0-1), where 1.0 is identical

## Model

Uses `all-MiniLM-L6-v2` by default:
- **Size**: ~80MB model download
- **Dimensions**: 384-dimensional embeddings
- **Speed**: Fast enough for real-time search
- **Quality**: Good balance of speed and accuracy

## Installation

### With Semantic Search (Recommended when you need it)

```bash
# Install full dependencies (includes PyTorch ~900MB)
./venv/bin/pip install -r requirements.txt

# Run with semantic search enabled
./venv/bin/python3 main.py --local-semantic
```

### Without Semantic Search (Default, faster startup)

```bash
# Install minimal dependencies
./venv/bin/pip install -r requirements-minimal.txt

# Run without semantic search (default behavior)
./venv/bin/python3 main.py
```

## Usage Examples

### Example 1: Authentication Questions

**You copy**: "How should we handle user login?"

**Semantic matches find**:
- Snippet about JWT implementation
- Sarah Mitchell (Auth Team Lead)
- OAuth discussion notes
- Mobile Auth Redesign project

Even though you didn't mention "JWT" or "OAuth", the semantic search understands that login relates to authentication concepts.

### Example 2: Performance Issues

**You copy**: "The API is slow, need to optimize"

**Semantic matches find**:
- Performance optimization notes (caching, Redis)
- John Chen (database optimization expert)
- Database threading fix snippet
- Benchmarking results

The tool understands "slow" and "optimize" relate to "performance" semantically.

### Example 3: UI Work

**You copy**: "Working on the dashboard layout"

**Semantic matches find**:
- Dashboard UI design notes
- Emma Rodriguez (Frontend Lead)
- React and TypeScript snippets
- Dark mode implementation notes

## Configuration

### Similarity Threshold

Control how strict matching is (in `config.yaml` or `config-markdown.yaml`):

```yaml
semantic_search:
  enabled: true
  model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.3  # 0.0 to 1.0
```

**Threshold values**:
- `0.1-0.3`: Very broad matching (more results, some less relevant)
- `0.4-0.5`: Balanced (good mix of recall and precision)
- `0.6-0.8`: Strict matching (fewer but highly relevant results)

### Changing the Model

You can use different sentence-transformer models:

```python
searcher = SemanticSearcher(
    db.connection,
    model_name='all-mpnet-base-v2',  # Higher quality, slower
    similarity_threshold=0.5
)
```

Popular alternatives:
- `all-mpnet-base-v2`: Better quality, larger model (~420MB)
- `paraphrase-MiniLM-L6-v2`: Optimized for paraphrases
- `multi-qa-MiniLM-L6-cos-v1`: Optimized for Q&A matching

## API Usage

### Generating Embeddings

```python
from src.semantic_searcher import SemanticSearcher

# Initialize
searcher = SemanticSearcher(db.connection)
searcher.initialize()

# Generate embeddings for all data
searcher.generate_embeddings_for_all()
```

### Finding Similar Items

```python
# Search by text
results = searcher.find_similar("How do we handle auth?", limit=5)

for result in results:
    print(f"{result['type']}: {result['text'][:60]}")
    print(f"  Similarity: {result['similarity']:.2f}")
```

### Finding Similar to an Entity

```python
# Find items similar to a specific snippet
results = searcher.find_similar_to_entity('snippet', snippet_id=42, limit=5)
```

## Integration with Context Analyzer

The semantic search integrates automatically:

```python
from src.context_analyzer import ContextAnalyzer

# Create analyzer with semantic search
analyzer = ContextAnalyzer(
    db.connection,
    pattern_matcher,
    action_suggester,
    semantic_searcher  # Optional, can be None
)

# Analyze text
result = analyzer.analyze("authentication tokens")

# Results include semantic matches
print(result['semantic_matches'])  # List of semantically similar items
```

## Testing

Run the semantic search tests:

```bash
./venv/bin/python3 tests/test_semantic_search.py
```

Tests include:
- Embedding generation
- Similarity calculations
- Threshold filtering
- Integration with context analyzer
- Real-world clipboard scenarios

## Performance

### First Run

- Downloads model (~80-900MB depending on PyTorch)
- Generates embeddings for all data (~1-2 seconds for 100 items)

### Subsequent Runs

- Embeddings stored in database
- Similarity search is fast (< 50ms for 100 items)
- Real-time performance for clipboard monitoring

### Optimization Tips

1. **Use file-based database** instead of `:memory:` to persist embeddings between runs
2. **Regenerate embeddings** when you add new data:
   ```python
   searcher.generate_embeddings_for_all()
   ```
3. **Increase threshold** if you're getting too many irrelevant results
4. **Decrease threshold** if you're missing relevant results

## Architecture

```
User copies text
      ↓
ContextAnalyzer.analyze()
      ↓
SemanticSearcher.find_similar()
      ↓
1. Encode query text → embedding (384 dimensions)
2. Load stored embeddings from database
3. Calculate cosine similarity (dot product)
4. Sort by similarity score
5. Filter by threshold
      ↓
Return top N results with scores
```

## Embeddings Storage

Embeddings are stored in the `embeddings` table:

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    entity_type TEXT,      -- 'contact', 'snippet', 'project'
    entity_id INTEGER,      -- ID of the entity
    embedding BLOB,         -- 384 float32 values as bytes
    text TEXT               -- Original text for reference
)
```

## Example Output

```json
{
  "semantic_matches": [
    {
      "type": "snippet",
      "id": 12,
      "text": "Discussed authentication implementation with Sarah...",
      "similarity": 0.82
    },
    {
      "type": "contact",
      "id": 3,
      "text": "Sarah Mitchell Auth Team Lead Leading authentication...",
      "similarity": 0.76
    },
    {
      "type": "project",
      "id": 2,
      "text": "Mobile Auth Redesign Implementing OAuth 2.0...",
      "similarity": 0.71
    }
  ]
}
```

## Benefits

✅ **Conceptual Understanding**: Finds related content even with different terminology
✅ **Knowledge Discovery**: Surfaces connections you might not have noticed
✅ **Context Aware**: Understands the meaning, not just keywords
✅ **Multi-lingual Support**: Works across different ways of expressing the same idea
✅ **Automatic**: No manual tagging or categorization required

## Limitations

⚠️ **Large Dependencies**: Requires PyTorch (~900MB)
⚠️ **Initial Setup**: First-time model download takes time
⚠️ **Memory Usage**: Embeddings stored in memory for fast search
⚠️ **Language**: Works best with English text (model dependent)

## Troubleshooting

### "Module 'sentence_transformers' not found"

Install the full requirements:
```bash
./venv/bin/pip install sentence-transformers numpy
```

### Slow First Run

The model downloads on first use (~80MB). Subsequent runs use cached model.

### No Results Found

- Lower the similarity threshold in config
- Check that embeddings were generated: `SELECT COUNT(*) FROM embeddings`
- Verify your query text is substantial (> 3 words works best)

### Out of Memory

- Use smaller model (all-MiniLM-L6-v2 is already small)
- Reduce number of stored embeddings
- Use file-based DB instead of `:memory:`

## Further Reading

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Semantic Search Explained](https://www.sbert.net/examples/applications/semantic-search/README.html)
- [Choosing the Right Model](https://www.sbert.net/docs/pretrained_models.html)
