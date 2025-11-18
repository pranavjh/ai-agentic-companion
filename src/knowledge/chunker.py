"""
Document Chunking System

Splits documents into chunks for efficient retrieval and embedding.
Uses LangChain text splitters with configurable chunk size and overlap.
"""

from typing import Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken


class DocumentChunker:
    """Chunk documents intelligently for RAG"""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        """
        Initialize chunker.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Use tiktoken for accurate token counting (GPT-4)
        self.encoding = tiktoken.encoding_for_model("gpt-4o")

        # Create text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],  # Try to split on natural boundaries
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))

    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Chunk a document into smaller pieces.

        Args:
            document: Dict with 'text' and metadata from PDF processor

        Returns:
            List of chunk dicts with text and metadata
        """
        text = document.get('text', '')

        if not text.strip():
            return []

        # Split text into chunks
        chunks = self.text_splitter.split_text(text)

        # Create chunk objects with metadata
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            chunk_obj = {
                'text': chunk_text,
                'chunk_index': idx,
                'total_chunks': len(chunks),

                # Preserve original document metadata
                'source_file': document.get('source_file', ''),
                'filename': document.get('filename', ''),
                'topic': document.get('topic', 'general'),
                'page_count': document.get('page_count', 0),

                # Chunk-specific metadata
                'chunk_token_count': self._count_tokens(chunk_text),
                'chunk_char_count': len(chunk_text),
            }

            chunk_objects.append(chunk_obj)

        return chunk_objects

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document dicts

        Returns:
            Flat list of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        return all_chunks

    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks.

        Args:
            chunks: List of chunk dicts

        Returns:
            Dict with statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_tokens_per_chunk': 0,
                'min_tokens': 0,
                'max_tokens': 0,
            }

        token_counts = [c['chunk_token_count'] for c in chunks]

        return {
            'total_chunks': len(chunks),
            'avg_tokens_per_chunk': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'total_tokens': sum(token_counts),
        }
