"""
Podcast Generator

Generates podcast episodes with transcripts and optional audio (MP3).
Supports: monologue (single speaker) and conversation (Q&A style)
"""

from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json
from openai import OpenAI
from rich.console import Console
from datetime import datetime
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))

from retrieval.retriever import KnowledgeRetriever
from retrieval.context_builder import ContextBuilder

console = Console()


class PodcastGenerator:
    """Generate podcast episodes with transcripts and audio"""

    # Available OpenAI TTS voices
    AVAILABLE_VOICES = {
        'alloy': 'Neutral, balanced voice',
        'echo': 'Male, clear and articulate',
        'fable': 'Male, warm and friendly',
        'onyx': 'Male, deep and authoritative',
        'nova': 'Female, warm and engaging',
        'shimmer': 'Female, bright and energetic'
    }

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize podcast generator.

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

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.secrets['OPENAI_API_KEY'])
        self.model = self.config['models']['llm']
        self.tts_model = self.config['models']['tts']

        # Podcast config
        podcast_config = self.config.get('podcast', {})
        self.sample_rate = podcast_config.get('sample_rate', 44100)

        # Agent config
        agent_config = self.config['agents']['podcast']
        self.temperature = agent_config.get('temperature', 0.8)
        self.max_tokens = agent_config.get('max_tokens', 4000)

        # Initialize retriever and context builder
        self.retriever = KnowledgeRetriever(config_path)
        self.context_builder = ContextBuilder()

        # Output directories
        self.output_dir = Path(self.config['output']['podcast']['directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        topic: str,
        length: int = 10,
        format_type: str = "conversation",
        host_voice: str = "onyx",
        guest_voice: str = "nova",
        generate_audio: bool = True,
        output_path: Optional[Path] = None
    ) -> Dict:
        """
        Generate podcast episode.

        Args:
            topic: Topic for the podcast
            length: Target length in minutes (default 10)
            format_type: 'monologue' (single speaker) or 'conversation' (Q&A style)
            host_voice: Voice for host/main speaker (alloy, echo, fable, onyx, nova, shimmer)
            guest_voice: Voice for guest (used in conversation format)
            generate_audio: Whether to generate MP3 audio file
            output_path: Optional custom output path for transcript

        Returns:
            Dict with transcript, audio path (if generated), and metadata
        """
        self.console.print(f"\n[bold blue]Generating {format_type} podcast about:[/bold blue] {topic}")
        self.console.print(f"[cyan]Length: ~{length} minutes | Audio: {'Yes' if generate_audio else 'Transcript only'}[/cyan]")

        # Validate voices
        if host_voice not in self.AVAILABLE_VOICES:
            raise ValueError(f"Invalid host voice. Choose from: {', '.join(self.AVAILABLE_VOICES.keys())}")
        if guest_voice not in self.AVAILABLE_VOICES:
            raise ValueError(f"Invalid guest voice. Choose from: {', '.join(self.AVAILABLE_VOICES.keys())}")

        # Retrieve relevant knowledge
        self.console.print("[yellow]Retrieving knowledge from corpus...[/yellow]")
        chunks = self.retriever.retrieve(topic, top_k=10)  # More chunks for longer content
        context_info = self.context_builder.build_context(chunks)

        self.console.print(f"[green]✓ Retrieved {len(chunks)} relevant chunks from {context_info['num_sources']} sources[/green]")

        # Generate script
        self.console.print(f"[yellow]Generating {format_type} script...[/yellow]")
        if format_type == "monologue":
            script = self._generate_monologue_script(topic, context_info, length, host_voice)
        elif format_type == "conversation":
            script = self._generate_conversation_script(topic, context_info, length, host_voice, guest_voice)
        else:
            raise ValueError(f"Unknown format: {format_type}. Use 'monologue' or 'conversation'")

        self.console.print(f"[green]✓ Script generated with {len(script['segments'])} segments[/green]")

        # Build transcript
        transcript = self._build_transcript(script, format_type)
        word_count = len(transcript.split())

        # Prepare result
        result = {
            'format': format_type,
            'topic': topic,
            'length': length,
            'script': script,
            'transcript': transcript,
            'word_count': word_count,
            'audio_path': None,
            'host_voice': host_voice,
            'guest_voice': guest_voice if format_type == "conversation" else None,
            'sources': context_info['sources'],
            'num_sources': context_info['num_sources'],
            'timestamp': datetime.now().isoformat()
        }

        # Save transcript
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = self._sanitize_filename(topic)
            base_filename = f"{timestamp}_{safe_topic}"
            transcript_path = self.output_dir / f"{base_filename}.txt"
        else:
            transcript_path = output_path.with_suffix('.txt')
            base_filename = transcript_path.stem

        self._save_transcript(result, transcript_path)
        self.console.print(f"[bold green]✓ Transcript saved to: {transcript_path}[/bold green]")

        # Generate audio if requested
        if generate_audio:
            self.console.print("[yellow]Generating audio with OpenAI TTS...[/yellow]")
            audio_path = self.output_dir / f"{base_filename}.mp3"
            self._generate_audio(script, format_type, audio_path, host_voice, guest_voice)
            result['audio_path'] = str(audio_path)
            self.console.print(f"[bold green]✓ Audio saved to: {audio_path}[/bold green]")

        self.console.print(f"[cyan]Word count: {word_count}[/cyan]")

        return result

    def _generate_monologue_script(
        self,
        topic: str,
        context_info: Dict,
        length: int,
        voice: str
    ) -> Dict:
        """Generate script for single-speaker monologue format"""

        target_words = length * 150  # Approximately 150 words per minute

        user_prompt = f"""Create a professional podcast monologue script about: {topic}

Requirements:
- Target length: approximately {target_words} words (~{length} minutes)
- Single speaker format (informative presentation)
- Tone: Professional, engaging, conversational
- Structure:
  * INTRO: Brief introduction (15-20 seconds) - introduce the topic and what will be covered
  * MAIN CONTENT: Well-structured main discussion with key insights
  * OUTRO: Brief conclusion (10-15 seconds) - summarize key takeaways

IMPORTANT: Base your content primarily on the knowledge base context below. Make it informative, engaging, and suitable for audio format.

Knowledge Base Context:
{context_info['context']}

{context_info['source_references']}

Return the content in this JSON format:
{{
    "intro": "Introduction text here...",
    "main_segments": [
        "First main segment...",
        "Second main segment...",
        "Third main segment..."
    ],
    "outro": "Conclusion text here..."
}}

Make it sound natural for spoken word, using conversational language."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional podcast script writer specializing in AI and technology topics. You create engaging, informative scripts suitable for audio presentation."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        content_text = response.choices[0].message.content.strip()

        # Parse JSON response
        if '```json' in content_text:
            content_text = content_text.split('```json')[1].split('```')[0].strip()
        elif '```' in content_text:
            content_text = content_text.split('```')[1].split('```')[0].strip()

        try:
            script_structure = json.loads(content_text)
        except json.JSONDecodeError:
            # Fallback
            self.console.print("[yellow]Warning: Could not parse JSON, using fallback structure[/yellow]")
            script_structure = {
                'intro': f"Welcome to today's discussion about {topic}.",
                'main_segments': [content_text],
                'outro': "Thank you for listening."
            }

        # Build segments list
        segments = []
        segments.append({'speaker': 'host', 'text': script_structure['intro']})
        for segment in script_structure['main_segments']:
            segments.append({'speaker': 'host', 'text': segment})
        segments.append({'speaker': 'host', 'text': script_structure['outro']})

        return {
            'intro': script_structure['intro'],
            'main_content': script_structure['main_segments'],
            'outro': script_structure['outro'],
            'segments': segments
        }

    def _generate_conversation_script(
        self,
        topic: str,
        context_info: Dict,
        length: int,
        host_voice: str,
        guest_voice: str
    ) -> Dict:
        """Generate script for two-person Q&A conversation format"""

        target_words = length * 150  # Approximately 150 words per minute
        num_exchanges = max(5, length // 2)  # More exchanges for longer podcasts

        user_prompt = f"""Create a professional podcast conversation script about: {topic}

Format: Q&A style conversation between a Host and a Guest expert.

Requirements:
- Target length: approximately {target_words} words (~{length} minutes)
- Two speakers: Host (interviewer) and Guest (expert)
- Tone: Professional yet conversational, engaging
- Structure:
  * INTRO: Host introduces the topic and guest (15-20 seconds)
  * CONVERSATION: {num_exchanges} Q&A exchanges covering key aspects
  * OUTRO: Host wraps up with key takeaways (10-15 seconds)

IMPORTANT: Base the guest's responses primarily on the knowledge base context below. Make it sound like a natural conversation.

Knowledge Base Context:
{context_info['context']}

{context_info['source_references']}

Return the content in this JSON format:
{{
    "intro": "Host introduction text...",
    "exchanges": [
        {{
            "host": "Host question or comment...",
            "guest": "Guest response..."
        }},
        ...
    ],
    "outro": "Host conclusion text..."
}}

Make it sound natural and conversational, like a real podcast interview."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional podcast script writer. You create engaging Q&A style conversations between a host and expert guest, making complex topics accessible and interesting."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        content_text = response.choices[0].message.content.strip()

        # Parse JSON response
        if '```json' in content_text:
            content_text = content_text.split('```json')[1].split('```')[0].strip()
        elif '```' in content_text:
            content_text = content_text.split('```')[1].split('```')[0].strip()

        try:
            script_structure = json.loads(content_text)
        except json.JSONDecodeError:
            self.console.print("[yellow]Warning: Could not parse JSON, using fallback structure[/yellow]")
            script_structure = {
                'intro': f"Welcome! Today we're discussing {topic}.",
                'exchanges': [
                    {'host': f"Tell us about {topic}.", 'guest': content_text}
                ],
                'outro': "Thanks for joining us today."
            }

        # Build segments list
        segments = []
        segments.append({'speaker': 'host', 'text': script_structure['intro']})
        for exchange in script_structure['exchanges']:
            segments.append({'speaker': 'host', 'text': exchange['host']})
            segments.append({'speaker': 'guest', 'text': exchange['guest']})
        segments.append({'speaker': 'host', 'text': script_structure['outro']})

        return {
            'intro': script_structure['intro'],
            'exchanges': script_structure['exchanges'],
            'outro': script_structure['outro'],
            'segments': segments
        }

    def _build_transcript(self, script: Dict, format_type: str) -> str:
        """Build formatted transcript"""

        lines = []

        # Add header
        lines.append("=" * 60)
        lines.append("PODCAST TRANSCRIPT")
        lines.append("=" * 60)
        lines.append("")

        # Add segments
        for segment in script['segments']:
            speaker_label = segment['speaker'].upper()
            if speaker_label == 'HOST':
                lines.append(f"HOST: {segment['text']}")
            elif speaker_label == 'GUEST':
                lines.append(f"GUEST: {segment['text']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("END OF TRANSCRIPT")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_audio(
        self,
        script: Dict,
        format_type: str,
        output_path: Path,
        host_voice: str,
        guest_voice: str
    ):
        """Generate MP3 audio file using OpenAI TTS"""

        # Combine all segments into one text for single audio generation
        # This avoids needing ffmpeg for combining audio files
        full_text_parts = []

        for segment in script['segments']:
            # Add brief pause markers between segments using punctuation
            full_text_parts.append(segment['text'] + "...")

        full_text = " ".join(full_text_parts)

        # For conversation format, we need to generate separate files
        # For monologue, single file works fine
        if format_type == "monologue":
            # Single speaker, generate one file
            self.console.print(f"[dim]  Generating audio with {host_voice} voice...[/dim]")

            response = self.client.audio.speech.create(
                model=self.tts_model,
                voice=host_voice,
                input=full_text,
                speed=1.0
            )

            # Save directly to file
            with open(output_path, 'wb') as f:
                f.write(response.content)

        else:
            # Conversation format - generate with host voice for simplicity
            # In a future version, could generate separate files per speaker
            self.console.print(f"[dim]  Generating audio with {host_voice} voice (conversation)...[/dim]")
            self.console.print(f"[yellow]  Note: Multi-voice conversation requires ffmpeg. Using single voice.[/yellow]")

            response = self.client.audio.speech.create(
                model=self.tts_model,
                voice=host_voice,
                input=full_text,
                speed=1.0
            )

            # Save directly to file
            with open(output_path, 'wb') as f:
                f.write(response.content)

        self.console.print(f"[dim]  Audio generation complete                [/dim]")

    def _save_transcript(self, result: Dict, output_path: Path):
        """Save transcript to file with metadata"""

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write the transcript
            f.write(result['transcript'])

            # Add metadata
            f.write("\n\n")
            f.write("=" * 60 + "\n")
            f.write("METADATA\n")
            f.write("=" * 60 + "\n")
            f.write(f"Topic: {result['topic']}\n")
            f.write(f"Format: {result['format']}\n")
            f.write(f"Target Length: {result['length']} minutes\n")
            f.write(f"Word Count: {result['word_count']}\n")
            f.write(f"Host Voice: {result['host_voice']}\n")
            if result['guest_voice']:
                f.write(f"Guest Voice: {result['guest_voice']}\n")
            f.write(f"Sources: {result['num_sources']} knowledge base sources\n")
            f.write(f"Generated: {result['timestamp']}\n")

            # Add sources
            if result['num_sources'] > 0:
                f.write("\n" + "=" * 60 + "\n")
                f.write("KNOWLEDGE BASE SOURCES\n")
                f.write("=" * 60 + "\n")
                for source in result['sources']:
                    f.write(f"{source['ref']}. {source['filename']} (Topic: {source['topic']})\n")

    def _sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        safe = re.sub(r'[^\w\s-]', '', text)
        safe = re.sub(r'[\s]+', '_', safe)
        safe = safe[:50]
        return safe.lower()


if __name__ == "__main__":
    # Test the podcast generator
    generator = PodcastGenerator()

    # Test monologue
    result = generator.generate(
        topic="The Future of AI Agents",
        length=3,
        format_type="monologue",
        host_voice="onyx",
        generate_audio=False
    )

    print(f"\n✓ Generated monologue podcast: {result['topic']}")
    print(f"  Words: {result['word_count']}")
    print(f"  Sources: {result['num_sources']}")
