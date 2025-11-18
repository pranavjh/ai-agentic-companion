"""
Q&A Agent

Orchestrates the question-answering process:
1. Retrieve relevant chunks from knowledge base
2. Build RAG context
3. Generate response with LLM (knowledge base + general knowledge)
4. Maintain conversation history
"""

from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json
from openai import OpenAI
from rich.console import Console

import sys
sys.path.append(str(Path(__file__).parent.parent))

from retrieval.retriever import KnowledgeRetriever
from retrieval.context_builder import ContextBuilder

console = Console()


class QAAgent:
    """Question-Answering Agent with RAG and conversation memory"""

    def __init__(self, config_path: str = "config/config.yaml", max_history: int = 10):
        """
        Initialize Q&A agent.

        Args:
            config_path: Path to configuration file
            max_history: Maximum number of conversation messages to keep (default 10)
        """
        self.console = console

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load secrets
        secrets_path = Path(config_path).parent / "secrets" / "config.json"
        with open(secrets_path, 'r') as f:
            self.secrets = json.load(f)

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.secrets['OPENAI_API_KEY'])
        self.model = self.config['models']['llm']

        # Agent configuration
        qa_config = self.config.get('agents', {}).get('qa', {})
        self.temperature = qa_config.get('temperature', 0.3)
        self.max_tokens = qa_config.get('max_tokens', 1000)

        # Initialize retriever and context builder
        self.retriever = KnowledgeRetriever(config_path)
        self.context_builder = ContextBuilder()

        # Conversation memory (list of messages)
        self.conversation_history = []
        self.max_history = max_history

    def add_to_history(self, role: str, content: str):
        """
        Add message to conversation history.

        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        self.conversation_history.append({
            'role': role,
            'content': content
        })

        # Trim history if exceeds max
        if len(self.conversation_history) > self.max_history:
            # Keep system message if present, then trim oldest messages
            if self.conversation_history[0]['role'] == 'system':
                # Keep system + last (max_history - 1) messages
                self.conversation_history = [self.conversation_history[0]] + \
                                           self.conversation_history[-(self.max_history - 1):]
            else:
                # Keep last max_history messages
                self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def answer(self, question: str, verbose: bool = False) -> Dict:
        """
        Answer a question using RAG + LLM verification.

        Args:
            question: User's question
            verbose: If True, return detailed information about retrieval

        Returns:
            Dict with answer and metadata
        """
        # Step 1: Retrieve relevant chunks
        chunks = self.retriever.retrieve(question)

        if verbose:
            self.console.print(f"\n[dim]Retrieved {len(chunks)} relevant chunks[/dim]")
            if chunks:
                sources = self.retriever.get_unique_sources(chunks)
                self.console.print(f"[dim]Sources: {', '.join(sources)}[/dim]\n")

        # Step 2: Build context
        context_info = self.context_builder.build_context(chunks)

        # Step 3: Build system prompt
        system_prompt = self.context_builder.build_system_prompt(context_info)

        # Step 4: Prepare messages for LLM
        messages = []

        # Add system prompt
        messages.append({
            'role': 'system',
            'content': system_prompt
        })

        # Add conversation history (excluding old system messages)
        for msg in self.conversation_history:
            if msg['role'] != 'system':  # Skip old system messages
                messages.append(msg)

        # Add current question
        messages.append({
            'role': 'user',
            'content': question
        })

        # Step 5: Generate response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content

            # Step 6: Update conversation history
            self.add_to_history('user', question)
            self.add_to_history('assistant', answer)

            # Step 7: Prepare response
            return {
                'answer': answer,
                'sources': context_info.get('sources', []),
                'has_kb_sources': context_info['has_relevant_info'],
                'num_chunks': context_info.get('num_chunks', 0),
                'chunks': chunks if verbose else [],
                'conversation_length': len(self.conversation_history)
            }

        except Exception as e:
            self.console.print(f"[red]Error generating response:[/red] {e}")
            return {
                'answer': f"I encountered an error while processing your question: {e}",
                'sources': [],
                'has_kb_sources': False,
                'num_chunks': 0,
                'chunks': [],
                'conversation_length': len(self.conversation_history)
            }

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.

        Returns:
            String summary
        """
        if not self.conversation_history:
            return "No conversation history"

        user_messages = [msg for msg in self.conversation_history if msg['role'] == 'user']
        assistant_messages = [msg for msg in self.conversation_history if msg['role'] == 'assistant']

        return f"{len(user_messages)} questions asked, {len(assistant_messages)} responses given"
