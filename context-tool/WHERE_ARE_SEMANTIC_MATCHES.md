# Where to See Semantic Matches in the Web UI

## Quick Answer

Semantic matches appear in the **"Semantically Similar"** section of the context panel on the right side of the web UI.

## Step-by-Step Guide

### 1. Start the Server with Semantic Search Enabled

```bash
# Use markdown mode (includes example data)
./venv/bin/python3 main.py --markdown
```

**Important**: Make sure you see this in the output:
```
🔍 Semantic search: enabled

🧠 Initializing semantic search...
   ✓ Model loaded successfully
📊 Generating embeddings for semantic search...
   ✓ Generated 16 embeddings (384-dimensional vectors)
   ✓ Semantic search ready!
```

### 2. Open Your Browser

Navigate to: **http://localhost:8000**

### 3. Select Text

In the left panel, select any text from the demo content. Try these examples:

#### Example 1: Select "Sarah Mitchell"
**What you'll see:**
- **Selected Text**: "Sarah Mitchell"
- **Exact Matches**: Contact record for Sarah
- **Semantically Similar**:
  - Snippets mentioning authentication (70% similar)
  - Projects related to auth (65% similar)
  - Other team members working on similar topics

#### Example 2: Select "authentication"
**What you'll see:**
- **Semantically Similar**:
  - `snippet`: Authentication Implementation Discussion (58% similar)
  - `snippet`: JWT Authentication Discussion (58% similar)
  - `project`: Mobile Auth Redesign (54% similar)
  - `contact`: Sarah Mitchell - Auth Team Lead (43% similar)

#### Example 3: Type Your Own Text
You can also paste any text in the demo text area to analyze it!

Try: "How do we handle user login and security?"

**What you'll see:**
- **Semantically Similar**:
  - Authentication-related snippets
  - OAuth and JWT discussions
  - Security team contacts
  - Related projects

## What the Semantic Section Looks Like

```
┌─────────────────────────────────────────────┐
│ Semantically Similar                        │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ snippet (58% similar)                   │ │
│ │ # Authentication Implementation         │ │
│ │ Discussion Met with Sarah to discuss... │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ project (54% similar)                   │ │
│ │ Mobile Auth Redesign # Mobile Auth...  │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

Each match shows:
- **Type** (snippet, contact, project)
- **Similarity percentage** (higher = more related)
- **Preview** of the content

## Troubleshooting

### "I don't see 'Semantically Similar' section"

**Possible causes:**

1. **Semantic search not enabled**
   - Check server output for "🔍 Semantic search: enabled"
   - If you see "disabled", restart with the `--local-semantic` flag

2. **No embeddings generated**
   - Check for "📊 Generated X embeddings" in server output
   - If 0 embeddings, make sure data directory has content

3. **Text too short**
   - Semantic search works best with 3+ words
   - Single words may not have enough context

4. **Similarity threshold too high**
   - Default threshold filters out low-similarity matches
   - In `config-markdown.yaml`, try lowering `similarity_threshold` to 0.2

### "Semantic search is very slow"

**First run**: Model downloads (~80MB), takes 30-60 seconds
**Subsequent runs**: Fast (< 1 second) - model is cached

### "Results don't seem relevant"

- Semantic search understands meaning, not exact keywords
- A 40-50% match can still be relevant
- Lower matches (< 30%) are filtered out by default
- Adjust `similarity_threshold` in config if needed

## Example Configuration

In `config-markdown.yaml`:

```yaml
semantic_search:
  enabled: true
  model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.3  # 0.0 to 1.0
  # Lower = more results (some less relevant)
  # Higher = fewer results (more precise)
```

## Visual Reference

### Full Web UI Layout

```
┌────────────────────────────┬────────────────────────────┐
│ Context Tool Demo          │ Context & Analysis         │
├────────────────────────────┼────────────────────────────┤
│                            │                            │
│ Select any text below:     │ Selected Text              │
│                            │ "authentication"           │
│ [Demo text with Sarah      │                            │
│  Mitchell, JT-344, etc.]   │ Semantically Similar       │
│                            │ ┌────────────────────────┐ │
│ <-- Select text here       │ │ snippet (58% similar)  │ │
│                            │ │ Auth Implementation... │ │
│                            │ └────────────────────────┘ │
│                            │ ┌────────────────────────┐ │
│                            │ │ project (54% similar)  │ │
│                            │ │ Mobile Auth Redesign   │ │
│                            │ └────────────────────────┘ │
│                            │                            │
│                            │ Exact Matches              │
│                            │ ...                        │
│                            │                            │
│                            │ Related Items              │
│                            │ ...                        │
└────────────────────────────┴────────────────────────────┘
```

## Quick Test

1. Start server: `./venv/bin/python3 main.py --markdown`
2. Open: http://localhost:8000
3. Select: "authentication" (in the demo text)
4. Look for: **"Semantically Similar"** section in right panel
5. Should see: 3-4 matches with percentages

If you see the section with matches, **it's working!** 🎉

## Advanced: Using Your Own Data

To see semantic matches for your own notes:

1. Add markdown files to `data-md/snippets/`, `data-md/people/`, etc.
2. Restart server
3. Server will generate embeddings for your new data
4. Select any text related to your notes
5. See semantic matches based on meaning, not just keywords!

---

**Summary**: Semantic matches appear in a section called **"Semantically Similar"** in the right panel of the web UI. They show related content based on meaning, with similarity percentages.
