"""
Ingestion Orchestrator

Coordinates the entire knowledge base ingestion pipeline:
- PDF processing
- Chunking
- Embedding generation
- Vector storage

Supports incremental updates (only processes new/modified files).
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel

from .pdf_processor import PDFProcessor
from .chunker import DocumentChunker
from .embedder import EmbeddingGenerator
from .vector_store import VectorStoreManager

console = Console()


class KnowledgeBaseIngester:
    """Orchestrate knowledge base ingestion pipeline"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize ingester.

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

        # Initialize components
        self.pdf_processor = PDFProcessor()

        chunking_config = self.config['chunking']
        self.chunker = DocumentChunker(
            chunk_size=chunking_config['chunk_size'],
            chunk_overlap=chunking_config['chunk_overlap']
        )

        self.embedder = EmbeddingGenerator(
            api_key=self.secrets['OPENAI_API_KEY'],
            model=self.config['models']['embedding'],
            batch_size=100
        )

        vector_db_config = self.config['vector_db']
        self.vector_store = VectorStoreManager(
            persist_directory=vector_db_config['persist_directory'],
            collection_name=vector_db_config['collection_name']
        )

        # Get corpus path
        self.corpus_path = Path(self.config['corpus']['path'])

    def find_pdf_files(self) -> List[Path]:
        """
        Find all PDF files in corpus.

        Returns:
            List of PDF file paths
        """
        if not self.corpus_path.exists():
            raise ValueError(f"Corpus path does not exist: {self.corpus_path}")

        pdf_files = list(self.corpus_path.rglob('*.pdf'))

        # Filter by max file size if configured
        max_size_mb = self.config['corpus'].get('max_file_size_mb', 50)
        filtered_files = []

        for pdf_file in pdf_files:
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            if size_mb <= max_size_mb:
                filtered_files.append(pdf_file)
            else:
                self.console.print(f"[yellow]Skipping {pdf_file.name} (too large: {size_mb:.1f}MB)[/yellow]")

        return filtered_files

    def filter_new_files(self, pdf_files: List[Path]) -> List[Path]:
        """
        Filter to only new or modified files.

        Args:
            pdf_files: List of all PDF files

        Returns:
            List of files that need processing
        """
        new_files = []

        for pdf_file in pdf_files:
            if not self.vector_store.is_file_processed(pdf_file):
                new_files.append(pdf_file)

        return new_files

    def ingest_file(self, pdf_path: Path) -> Optional[int]:
        """
        Ingest a single PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of chunks added, or None if failed
        """
        # Extract text
        document = self.pdf_processor.process_pdf_with_metadata(pdf_path, self.corpus_path)

        if not document:
            return None

        # Chunk document
        chunks = self.chunker.chunk_document(document)

        if not chunks:
            self.console.print(f"[yellow]No chunks created from {pdf_path.name}[/yellow]")
            return None

        # Generate embeddings
        embedded_chunks = self.embedder.generate_embeddings(chunks, show_progress=False)

        # Add to vector store
        num_added = self.vector_store.add_chunks(embedded_chunks)

        if num_added > 0:
            # Mark file as processed
            self.vector_store.mark_file_processed(pdf_path, num_added)

        return num_added

    def ingest_corpus(self, force_reindex: bool = False, batch_size: int = 10):
        """
        Ingest entire corpus with progress tracking.

        Args:
            force_reindex: If True, reprocess all files (ignoring processed status)
            batch_size: Number of files to process before showing stats
        """
        self.console.print(Panel.fit(
            "[bold cyan]Knowledge Base Ingestion[/bold cyan]\n"
            f"Corpus: {self.corpus_path}",
            border_style="cyan"
        ))

        # Find PDF files
        self.console.print("\n[yellow]Scanning for PDF files...[/yellow]")
        all_pdf_files = self.find_pdf_files()
        self.console.print(f"[green]Found {len(all_pdf_files)} PDF files[/green]")

        # Filter to new files (unless force reindex)
        if force_reindex:
            files_to_process = all_pdf_files
            self.console.print("[yellow]Force reindex enabled - processing all files[/yellow]")
        else:
            files_to_process = self.filter_new_files(all_pdf_files)
            already_processed = len(all_pdf_files) - len(files_to_process)
            self.console.print(f"[green]{already_processed} files already processed[/green]")
            self.console.print(f"[cyan]{len(files_to_process)} new/modified files to process[/cyan]\n")

        if not files_to_process:
            self.console.print("[green]✓ Knowledge base is up to date![/green]")
            self._show_stats()
            return

        # Process files with progress bar
        successful = 0
        failed = 0
        total_chunks = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Processing {len(files_to_process)} files...",
                total=len(files_to_process)
            )

            for pdf_file in files_to_process:
                try:
                    num_chunks = self.ingest_file(pdf_file)

                    if num_chunks is not None and num_chunks > 0:
                        successful += 1
                        total_chunks += num_chunks
                    else:
                        failed += 1

                except Exception as e:
                    self.console.print(f"[red]Error processing {pdf_file.name}:[/red] {e}")
                    failed += 1

                progress.update(task, advance=1)

        # Show results
        self.console.print("\n[bold green]Ingestion Complete![/bold green]\n")

        results_table = Table(show_header=True, header_style="bold cyan")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")

        results_table.add_row("Files Processed", str(successful))
        results_table.add_row("Files Failed", str(failed) if failed > 0 else "[green]0[/green]")
        results_table.add_row("Chunks Added", str(total_chunks))

        self.console.print(results_table)
        self.console.print()

        # Show vector store stats
        self._show_stats()

    def _show_stats(self):
        """Display vector store statistics"""
        stats = self.vector_store.get_stats()

        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Vector Store Stats", style="magenta")
        stats_table.add_column("Value", style="yellow", justify="right")

        stats_table.add_row("Total Chunks in DB", str(stats['total_chunks']))
        stats_table.add_row("Total Files Processed", str(stats['processed_files']))
        stats_table.add_row("Collection Name", stats['collection_name'])

        self.console.print(stats_table)
        self.console.print()


def main():
    """Main entry point for standalone execution"""
    ingester = KnowledgeBaseIngester()
    ingester.ingest_corpus()


if __name__ == "__main__":
    main()
