"""
PDF Text Processor

Extracts text from PDFs (no OCR - text only, ignores images/bitmaps).
Handles errors gracefully and extracts metadata.
"""

from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
from pypdf2 import PdfReader
from rich.console import Console

console = Console()


class PDFProcessor:
    """Process PDF files and extract text content"""

    def __init__(self):
        self.console = console

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        Extract text from a PDF file (no OCR, text only).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with extracted text and metadata, or None if failed
        """
        try:
            # Try pdfplumber first (better text extraction)
            return self._extract_with_pdfplumber(pdf_path)
        except Exception as e:
            # Fallback to PyPDF2
            try:
                return self._extract_with_pypdf2(pdf_path)
            except Exception as e2:
                self.console.print(f"[red]Error processing {pdf_path.name}:[/red] {e2}")
                return None

    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict:
        """Extract text using pdfplumber (preferred method)"""
        text_pages = []
        page_count = 0

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text only (ignores images)
                text = page.extract_text()

                if text and text.strip():
                    text_pages.append({
                        'page_number': page_num,
                        'text': text.strip()
                    })

        # Combine all pages
        full_text = "\n\n".join([p['text'] for p in text_pages])

        if not full_text.strip():
            raise ValueError(f"No text content found in {pdf_path.name}")

        return {
            'text': full_text,
            'page_count': page_count,
            'pages_with_text': len(text_pages),
            'source_file': str(pdf_path),
            'filename': pdf_path.name
        }

    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict:
        """Fallback: Extract text using PyPDF2"""
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)

        text_pages = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if text and text.strip():
                text_pages.append({
                    'page_number': page_num,
                    'text': text.strip()
                })

        full_text = "\n\n".join([p['text'] for p in text_pages])

        if not full_text.strip():
            raise ValueError(f"No text content found in {pdf_path.name}")

        return {
            'text': full_text,
            'page_count': page_count,
            'pages_with_text': len(text_pages),
            'source_file': str(pdf_path),
            'filename': pdf_path.name
        }

    def get_topic_from_path(self, pdf_path: Path, corpus_root: Path) -> str:
        """
        Extract topic from subfolder structure.

        Args:
            pdf_path: Path to PDF file
            corpus_root: Root path of corpus

        Returns:
            Topic name (subfolder name) or 'general'
        """
        try:
            relative = pdf_path.relative_to(corpus_root)
            if len(relative.parts) > 1:
                return relative.parts[0]  # First subfolder
            return 'general'
        except ValueError:
            return 'general'

    def process_pdf_with_metadata(self, pdf_path: Path, corpus_root: Path) -> Optional[Dict]:
        """
        Process PDF and add enriched metadata.

        Args:
            pdf_path: Path to PDF file
            corpus_root: Root path of corpus

        Returns:
            Dict with text and metadata, or None if failed
        """
        result = self.extract_text_from_pdf(pdf_path)

        if result:
            # Add topic metadata
            result['topic'] = self.get_topic_from_path(pdf_path, corpus_root)

            # Add file size
            result['file_size_mb'] = pdf_path.stat().st_size / (1024 * 1024)

            # Character and word counts
            result['char_count'] = len(result['text'])
            result['word_count'] = len(result['text'].split())

        return result
