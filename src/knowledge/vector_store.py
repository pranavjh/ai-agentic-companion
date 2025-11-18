"""
Vector Store Manager

Manages ChromaDB vector database with support for incremental updates.
Tracks processed files to avoid reprocessing.
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import hashlib
from datetime import datetime
import chromadb
from chromadb.config import Settings
from rich.console import Console

console = Console()


class VectorStoreManager:
    """Manage ChromaDB vector store with incremental updates"""

    def __init__(self, persist_directory: str, collection_name: str = "ai_agentic_knowledge"):
        """
        Initialize vector store manager.

        Args:
            persist_directory: Directory to persist ChromaDB
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name
        self.console = console

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "AI and Agentic knowledge base"}
        )

        # Metadata tracking file
        self.metadata_file = self.persist_directory.parent / "processed_files.json"
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self) -> Dict:
        """Load processed files metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_files(self):
        """Save processed files metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def compute_file_hash(self, file_path: Path) -> str:
        """
        Compute MD5 hash of file for change detection.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash string
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def is_file_processed(self, file_path: Path) -> bool:
        """
        Check if file has already been processed.

        Args:
            file_path: Path to PDF file

        Returns:
            True if file is already processed and unchanged
        """
        file_key = str(file_path)

        if file_key not in self.processed_files:
            return False

        # Check if file hash matches
        current_hash = self.compute_file_hash(file_path)
        stored_hash = self.processed_files[file_key].get('file_hash', '')

        return current_hash == stored_hash

    def mark_file_processed(self, file_path: Path, num_chunks: int):
        """
        Mark file as processed.

        Args:
            file_path: Path to PDF file
            num_chunks: Number of chunks created from this file
        """
        file_key = str(file_path)
        file_hash = self.compute_file_hash(file_path)

        self.processed_files[file_key] = {
            'file_hash': file_hash,
            'processed_date': datetime.now().isoformat(),
            'num_chunks': num_chunks,
            'filename': file_path.name
        }

        self._save_processed_files()

    def delete_file_chunks(self, file_path: Path):
        """
        Delete all chunks from a specific file (for updates).

        Args:
            file_path: Path to PDF file
        """
        file_key = str(file_path)

        # Query chunks from this file
        try:
            results = self.collection.get(
                where={"source_file": file_key}
            )

            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                self.console.print(f"[yellow]Deleted {len(results['ids'])} old chunks from {Path(file_key).name}[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error deleting chunks:[/red] {e}")

    def add_chunks(self, chunks: List[Dict]) -> int:
        """
        Add chunks to vector store.

        Args:
            chunks: List of chunk dicts with 'embedding' field

        Returns:
            Number of chunks successfully added
        """
        if not chunks:
            return 0

        # Filter chunks that have embeddings
        valid_chunks = [c for c in chunks if c.get('embedding') is not None]

        if not valid_chunks:
            self.console.print("[yellow]No valid chunks with embeddings to add[/yellow]")
            return 0

        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(valid_chunks):
            # Create unique ID for chunk
            chunk_id = f"{chunk['filename']}_{chunk['chunk_index']}"

            ids.append(chunk_id)
            embeddings.append(chunk['embedding'])
            documents.append(chunk['text'])

            # Store metadata (exclude embedding and text)
            metadata = {
                k: v for k, v in chunk.items()
                if k not in ['embedding', 'text'] and v is not None
            }
            # Ensure all metadata values are strings or numbers
            metadata = {k: str(v) if not isinstance(v, (int, float, bool)) else v
                       for k, v in metadata.items()}

            metadatas.append(metadata)

        try:
            # Add to collection (upsert behavior)
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            return len(valid_chunks)

        except Exception as e:
            self.console.print(f"[red]Error adding chunks to vector store:[/red] {e}")
            return 0

    def get_stats(self) -> Dict:
        """
        Get statistics about vector store.

        Returns:
            Dict with statistics
        """
        try:
            count = self.collection.count()
            num_files = len(self.processed_files)

            return {
                'total_chunks': count,
                'processed_files': num_files,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            self.console.print(f"[red]Error getting stats:[/red] {e}")
            return {
                'total_chunks': 0,
                'processed_files': 0,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }

    def query(self, query_embeddings: List[List[float]], top_k: int = 5) -> Dict:
        """
        Query vector store.

        Args:
            query_embeddings: List of query embedding vectors
            top_k: Number of results to return

        Returns:
            Query results
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k
            )
            return results
        except Exception as e:
            self.console.print(f"[red]Error querying vector store:[/red] {e}")
            return {}
