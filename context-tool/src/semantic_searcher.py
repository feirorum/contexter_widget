"""LLM-enhanced semantic similarity search"""

import sqlite3
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer


class SemanticSearcher:
    """Semantic similarity search using embeddings"""

    def __init__(
        self,
        db: sqlite3.Connection,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_threshold: float = 0.5
    ):
        """
        Initialize semantic searcher

        Args:
            db: Database connection
            model_name: SentenceTransformer model name
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.db = db
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.model: Optional[SentenceTransformer] = None
        self.embeddings: List[Dict] = []

    def initialize(self):
        """Initialize the model and load embeddings (lazy loading)"""
        if self.model is None:
            print(f"Loading semantic model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self._load_embeddings()
            print(f"Loaded {len(self.embeddings)} embeddings")

    def _load_embeddings(self):
        """Load pre-computed embeddings from database"""
        cursor = self.db.execute("SELECT * FROM embeddings")
        self.embeddings = []

        for row in cursor.fetchall():
            try:
                embedding_bytes = row['embedding']
                embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)

                self.embeddings.append({
                    'entity_type': row['entity_type'],
                    'entity_id': row['entity_id'],
                    'text': row['text'],
                    'embedding': embedding_array
                })
            except Exception as e:
                print(f"Warning: Failed to load embedding {row['id']}: {e}")

    def generate_embeddings_for_all(self):
        """
        Generate embeddings for all contacts, snippets, and projects

        This should be called after loading data into the database
        """
        if self.model is None:
            self.initialize()

        # Clear existing embeddings
        self.db.execute("DELETE FROM embeddings")

        # Generate embeddings for contacts
        cursor = self.db.execute("SELECT id, name, role, context FROM contacts")
        for row in cursor.fetchall():
            # Combine relevant fields for embedding
            text_parts = []
            if row['name']:
                text_parts.append(row['name'])
            if row['role']:
                text_parts.append(row['role'])
            if row['context']:
                text_parts.append(row['context'])

            text = ' '.join(text_parts)
            if text.strip():
                self._store_embedding('contact', row['id'], text)

        # Generate embeddings for snippets
        cursor = self.db.execute("SELECT id, text FROM snippets")
        for row in cursor.fetchall():
            if row['text']:
                self._store_embedding('snippet', row['id'], row['text'])

        # Generate embeddings for projects
        cursor = self.db.execute("SELECT id, name, description FROM projects")
        for row in cursor.fetchall():
            text_parts = []
            if row['name']:
                text_parts.append(row['name'])
            if row['description']:
                text_parts.append(row['description'])

            text = ' '.join(text_parts)
            if text.strip():
                self._store_embedding('project', row['id'], text)

        self.db.commit()

        # Reload embeddings into memory
        self._load_embeddings()

        print(f"Generated {len(self.embeddings)} embeddings")

    def _store_embedding(self, entity_type: str, entity_id: int, text: str):
        """Generate and store embedding for an entity"""
        embedding = self.model.encode(text)
        embedding_bytes = embedding.astype(np.float32).tobytes()

        self.db.execute("""
            INSERT INTO embeddings (entity_type, entity_id, embedding, text)
            VALUES (?, ?, ?, ?)
        """, (entity_type, entity_id, embedding_bytes, text))

    def find_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Find semantically similar items

        Args:
            query: Query text
            limit: Maximum number of results

        Returns:
            List of similar items with scores
        """
        if self.model is None:
            self.initialize()

        if not self.embeddings:
            return []

        # Encode query
        query_embedding = self.model.encode(query)

        # Calculate similarities
        similarities = []
        for item in self.embeddings:
            # Cosine similarity via dot product (embeddings are normalized)
            similarity = np.dot(query_embedding, item['embedding'])
            similarities.append((similarity, item))

        # Sort by similarity (descending)
        similarities.sort(reverse=True, key=lambda x: x[0])

        # Filter by threshold and return top results
        results = []
        for score, item in similarities[:limit]:
            if score >= self.similarity_threshold:
                results.append({
                    'type': item['entity_type'],
                    'id': item['entity_id'],
                    'text': item['text'],
                    'similarity': float(score)
                })

        return results

    def find_similar_to_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find items similar to a specific entity

        Args:
            entity_type: Type of entity (contact, snippet, project)
            entity_id: ID of entity
            limit: Maximum number of results

        Returns:
            List of similar items
        """
        if self.model is None:
            self.initialize()

        # Find the entity's embedding
        entity_embedding = None
        for item in self.embeddings:
            if item['entity_type'] == entity_type and item['entity_id'] == entity_id:
                entity_embedding = item['embedding']
                break

        if entity_embedding is None:
            return []

        # Calculate similarities
        similarities = []
        for item in self.embeddings:
            # Skip the entity itself
            if item['entity_type'] == entity_type and item['entity_id'] == entity_id:
                continue

            similarity = np.dot(entity_embedding, item['embedding'])
            similarities.append((similarity, item))

        # Sort and filter
        similarities.sort(reverse=True, key=lambda x: x[0])

        results = []
        for score, item in similarities[:limit]:
            if score >= self.similarity_threshold:
                results.append({
                    'type': item['entity_type'],
                    'id': item['entity_id'],
                    'text': item['text'],
                    'similarity': float(score)
                })

        return results
