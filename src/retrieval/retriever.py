"""
Retriever

Queries the vector database to retrieve relevant chunks for a given question.
"""

from typing import List, Dict
from pathlib import Path
import yaml
import json
from openai import OpenAI
from rich.console import Console

from knowledge.vector_store import VectorStoreManager

console = Console()


class KnowledgeRetriever:
    """Retrieve relevant knowledge from vector database"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize retriever.

        Args:
            config_path: Path to configuration file
        """
        self.console = console

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load secrets
        secrets_path = Path(config_path).parent / "secrets" / "config.json"
        with open(secrets_path, 'r') as f:
            self.secrets = json.load(f)

        # Initialize OpenAI client for embeddings
        self.client = OpenAI(api_key=self.secrets['OPENAI_API_KEY'])
        self.embedding_model = self.config['models']['embedding']

        # Initialize vector store
        vector_db_config = self.config['vector_db']
        self.vector_store = VectorStoreManager(
            persist_directory=vector_db_config['persist_directory'],
            collection_name=vector_db_config['collection_name']
        )

        # Retrieval settings
        retrieval_config = self.config.get('retrieval', {})
        self.top_k = retrieval_config.get('top_k', 5)
        self.similarity_threshold = retrieval_config.get('similarity_threshold', 0.7)

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for query.

        Args:
            query: User's question

        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            input=query,
            model=self.embedding_model
        )
        return response.data[0].embedding

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User's question
            top_k: Number of chunks to retrieve (overrides default)

        Returns:
            List of relevant chunks with metadata
        """
        k = top_k if top_k is not None else self.top_k

        # Generate query embedding
        query_embedding = self.embed_query(query)

        # Query vector store
        results = self.vector_store.query(
            query_embeddings=[query_embedding],
            top_k=k
        )

        # Format results
        chunks = []
        if results and 'documents' in results and results['documents']:
            for i in range(len(results['documents'][0])):
                chunk = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if 'metadatas' in results else {},
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                }

                # Calculate similarity score (ChromaDB uses L2 distance, convert to similarity)
                if chunk['distance'] is not None:
                    # Smaller distance = higher similarity
                    # Convert L2 distance to approximate cosine similarity
                    chunk['similarity'] = 1 / (1 + chunk['distance'])
                else:
                    chunk['similarity'] = 0.0

                chunks.append(chunk)

        # Filter by similarity threshold
        filtered_chunks = [
            c for c in chunks
            if c['similarity'] >= self.similarity_threshold
        ]

        return filtered_chunks

    def get_unique_sources(self, chunks: List[Dict]) -> List[str]:
        """
        Get unique source filenames from chunks.

        Args:
            chunks: List of retrieved chunks

        Returns:
            List of unique source filenames
        """
        sources = set()
        for chunk in chunks:
            filename = chunk.get('metadata', {}).get('filename', 'Unknown')
            sources.add(filename)

        return sorted(list(sources))
