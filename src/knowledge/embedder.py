"""
Embedding Generator

Generates embeddings for text chunks using OpenAI's embedding models.
Supports batch processing for efficiency.
"""

from typing import List, Dict
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import time

console = Console()


class EmbeddingGenerator:
    """Generate embeddings using OpenAI"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-large", batch_size: int = 100):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key
            model: Embedding model to use
            batch_size: Number of texts to embed in one API call
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self.console = console

    def generate_embeddings(self, chunks: List[Dict], show_progress: bool = True) -> List[Dict]:
        """
        Generate embeddings for chunks.

        Args:
            chunks: List of chunk dicts with 'text' field
            show_progress: Show progress bar

        Returns:
            Same chunks with 'embedding' field added
        """
        if not chunks:
            return []

        total_chunks = len(chunks)
        embedded_chunks = []

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            ) as progress:
                task = progress.add_task(
                    f"Generating embeddings ({self.model})...",
                    total=total_chunks
                )

                embedded_chunks = self._process_chunks_in_batches(chunks, progress, task)
        else:
            embedded_chunks = self._process_chunks_in_batches(chunks, None, None)

        return embedded_chunks

    def _process_chunks_in_batches(
        self,
        chunks: List[Dict],
        progress: Progress = None,
        task = None
    ) -> List[Dict]:
        """Process chunks in batches for efficiency"""
        embedded_chunks = []

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            texts = [chunk['text'] for chunk in batch]

            # Generate embeddings for batch
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model
                )

                # Add embeddings to chunks
                for j, chunk in enumerate(batch):
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding['embedding'] = response.data[j].embedding
                    embedded_chunks.append(chunk_with_embedding)

                # Update progress
                if progress and task is not None:
                    progress.update(task, advance=len(batch))

                # Rate limiting - small delay between batches
                if i + self.batch_size < len(chunks):
                    time.sleep(0.1)

            except Exception as e:
                self.console.print(f"[red]Error generating embeddings for batch {i//self.batch_size + 1}:[/red] {e}")
                # Add chunks without embeddings to preserve data
                for chunk in batch:
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding['embedding'] = None
                    embedded_chunks.append(chunk_with_embedding)

                if progress and task is not None:
                    progress.update(task, advance=len(batch))

        return embedded_chunks

    def get_embedding_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about embeddings.

        Args:
            chunks: List of chunks with embeddings

        Returns:
            Dict with statistics
        """
        total = len(chunks)
        embedded = sum(1 for c in chunks if c.get('embedding') is not None)

        return {
            'total_chunks': total,
            'successfully_embedded': embedded,
            'failed': total - embedded,
            'success_rate': (embedded / total * 100) if total > 0 else 0,
        }
