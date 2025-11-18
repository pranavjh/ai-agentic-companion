"""
Context Builder

Builds RAG context from retrieved chunks with proper formatting and citations.
"""

from typing import List, Dict


class ContextBuilder:
    """Build context for RAG from retrieved chunks"""

    def __init__(self):
        """Initialize context builder"""
        pass

    def build_context(self, chunks: List[Dict]) -> Dict:
        """
        Build context from retrieved chunks.

        Args:
            chunks: List of retrieved chunks with metadata

        Returns:
            Dict with formatted context and source mapping
        """
        if not chunks:
            return {
                'context': '',
                'sources': [],
                'has_relevant_info': False
            }

        # Create source mapping (filename -> reference number)
        unique_sources = {}
        source_list = []
        ref_num = 1

        for chunk in chunks:
            filename = chunk.get('metadata', {}).get('filename', 'Unknown')
            if filename not in unique_sources:
                unique_sources[filename] = ref_num
                source_list.append({
                    'ref': ref_num,
                    'filename': filename,
                    'topic': chunk.get('metadata', {}).get('topic', 'General')
                })
                ref_num += 1

        # Build context with inline citations
        context_parts = []
        context_parts.append("# Knowledge Base Context\n")

        for i, chunk in enumerate(chunks, 1):
            filename = chunk.get('metadata', {}).get('filename', 'Unknown')
            ref_number = unique_sources[filename]

            context_parts.append(f"\n## Source [{ref_number}] - Excerpt {i}:")
            context_parts.append(f"{chunk['text']}\n")

        # Combine context
        full_context = "\n".join(context_parts)

        # Build source reference section
        source_refs = "\n# Source References:\n"
        for src in source_list:
            source_refs += f"[{src['ref']}] {src['filename']} (Topic: {src['topic']})\n"

        return {
            'context': full_context,
            'source_references': source_refs,
            'sources': source_list,
            'has_relevant_info': len(chunks) > 0,
            'num_sources': len(source_list),
            'num_chunks': len(chunks)
        }

    def build_system_prompt(self, context_info: Dict) -> str:
        """
        Build system prompt for the LLM emphasizing knowledge base first.

        Args:
            context_info: Context information from build_context()

        Returns:
            System prompt string
        """
        if not context_info['has_relevant_info']:
            # No relevant knowledge base info
            return """You are an AI assistant specializing in AI and Agentic systems.

The knowledge base did not contain relevant information for this question.

Please provide a helpful answer based on your general knowledge, clearly stating that this is from your training data and not from the specific knowledge base.

Be concise and accurate."""

        # Has knowledge base context
        return f"""You are an AI assistant specializing in AI and Agentic systems.

You have access to a knowledge base of {context_info['num_chunks']} relevant excerpts from {context_info['num_sources']} documents.

IMPORTANT INSTRUCTIONS:
1. PRIMARY SOURCE: Answer the question primarily using the knowledge base context provided below
2. CITATIONS: Use inline citations [1], [2], etc. to reference knowledge base sources
3. ENHANCEMENT: After addressing the question with the knowledge base, you may:
   - Add recent developments or updates from your general knowledge
   - Provide additional context or explanations
   - Verify or extend the information
4. DISTINCTION: Clearly distinguish between:
   - Information from the knowledge base (use citations like [1])
   - Information from your general knowledge (indicate as "Additionally..." or "Based on general knowledge...")
5. ACCURACY: If knowledge base and general knowledge conflict, trust the knowledge base first

{context_info['context']}

{context_info['source_references']}

Remember: Knowledge base first, then enhance with general knowledge if helpful."""

    def format_sources_for_display(self, sources: List[Dict], include_general: bool = False) -> str:
        """
        Format sources for display in chat.

        Args:
            sources: List of source dicts
            include_general: Whether to include general knowledge indicator

        Returns:
            Formatted source string
        """
        if not sources and not include_general:
            return ""

        lines = ["\n📚 Sources:"]

        for src in sources:
            lines.append(f"  [{src['ref']}] {src['filename']}")

        if include_general:
            lines.append(f"  [LLM] General knowledge (GPT-4o)")

        return "\n".join(lines)
