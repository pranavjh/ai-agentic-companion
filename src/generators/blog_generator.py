"""
Blog Generator

Generates professional blog articles with RAG support and banner images.
Supports: short (~500 words), medium (~1000 words), long (~1500-2000 words)
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


class BlogGenerator:
    """Generate professional blog articles with banner images"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize blog generator.

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

        # Blog config
        blog_config = self.config.get('blog', {})
        self.format = blog_config.get('format', 'markdown')
        self.include_toc = blog_config.get('include_toc', True)
        self.include_citations = blog_config.get('include_citations', True)
        self.tone = blog_config.get('tone', 'informative')

        # Agent config
        agent_config = self.config['agents']['blog']
        self.temperature = agent_config.get('temperature', 0.7)
        self.max_tokens = agent_config.get('max_tokens', 3000)

        # Initialize retriever and context builder
        self.retriever = KnowledgeRetriever(config_path)
        self.context_builder = ContextBuilder()

        # Output directory
        self.output_dir = Path(self.config['output']['blog']['directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Banner images directory
        self.banner_dir = self.output_dir / "banners"
        self.banner_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        topic: str,
        length: str = "medium",
        create_banner: bool = True,
        output_path: Optional[Path] = None
    ) -> Dict:
        """
        Generate blog article.

        Args:
            topic: Topic for the blog
            length: 'short' (~500 words), 'medium' (~1000 words), or 'long' (~1500-2000 words)
            create_banner: Whether to generate banner image with DALL-E 3
            output_path: Optional custom output path

        Returns:
            Dict with blog content, metadata, and banner path
        """
        self.console.print(f"\n[bold cyan]Generating {length} blog article about:[/bold cyan] {topic}")

        # Retrieve relevant knowledge
        self.console.print("[yellow]Retrieving knowledge from corpus...[/yellow]")
        chunks = self.retriever.retrieve(topic, top_k=8)  # More chunks for longer content
        context_info = self.context_builder.build_context(chunks)

        self.console.print(f"[green]✓ Retrieved {len(chunks)} relevant chunks from {context_info['num_sources']} sources[/green]")

        # Generate blog content
        self.console.print("[yellow]Generating blog article...[/yellow]")
        blog_content = self._generate_blog_content(topic, context_info, length)

        # Generate banner image if requested
        banner_path = None
        if create_banner:
            self.console.print("[yellow]Generating banner image with DALL-E 3...[/yellow]")
            banner_path = self._generate_banner_image(topic, blog_content['title'])
            self.console.print(f"[green]✓ Banner image saved: {banner_path}[/green]")

        # Build final markdown
        markdown = self._build_markdown(blog_content, context_info, banner_path)

        # Count words
        word_count = len(markdown.split())

        # Prepare result
        result = {
            'format': 'blog',
            'topic': topic,
            'length': length,
            'title': blog_content['title'],
            'content': markdown,
            'word_count': word_count,
            'banner_path': str(banner_path) if banner_path else None,
            'sources': context_info['sources'],
            'num_sources': context_info['num_sources'],
            'timestamp': datetime.now().isoformat()
        }

        # Save to file
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = self._sanitize_filename(topic)
            filename = f"{timestamp}_{safe_topic}.md"
            output_path = self.output_dir / filename

        self._save_blog(result, output_path)
        self.console.print(f"[bold green]✓ Blog saved to: {output_path}[/bold green]")
        self.console.print(f"[cyan]Word count: {word_count}[/cyan]")

        return result

    def _generate_blog_content(self, topic: str, context_info: Dict, length: str) -> Dict:
        """Generate the main blog content using LLM"""

        # Determine target word count
        target_words = {
            'short': 500,
            'medium': 1000,
            'long': 1800
        }.get(length, 1000)

        # Determine number of sections
        num_sections = {
            'short': 3,
            'medium': 5,
            'long': 7
        }.get(length, 5)

        # Build prompt
        user_prompt = f"""Create a professional and informative blog article about: {topic}

Requirements:
- Target length: approximately {target_words} words
- Tone: Professional, informative, and engaging
- Structure:
  * Compelling title
  * Introduction (hook and overview)
  * {num_sections} main sections with clear headings
  * Conclusion with key takeaways
- Use the knowledge base context provided
- Include specific examples and insights
- Make it actionable and valuable for readers

IMPORTANT: Base your content primarily on the knowledge base context below. You may supplement with recent developments or general knowledge where appropriate, but clearly distinguish between knowledge base content and general knowledge.

Knowledge Base Context:
{context_info['context']}

{context_info['source_references']}

Return the content in this JSON format:
{{
    "title": "The blog title",
    "introduction": "The introduction paragraph(s)",
    "sections": [
        {{"heading": "Section 1 Heading", "content": "Section 1 content..."}},
        {{"heading": "Section 2 Heading", "content": "Section 2 content..."}}
    ],
    "conclusion": "The conclusion paragraph(s)"
}}

Ensure each section is substantial and informative."""

        # Generate with LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional technical writer specializing in AI and technology topics. You create well-structured, informative blog articles."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        content_text = response.choices[0].message.content.strip()

        # Parse JSON response
        # Extract JSON from markdown code blocks if present
        if '```json' in content_text:
            content_text = content_text.split('```json')[1].split('```')[0].strip()
        elif '```' in content_text:
            content_text = content_text.split('```')[1].split('```')[0].strip()

        try:
            blog_structure = json.loads(content_text)
        except json.JSONDecodeError:
            # Fallback: treat as plain text
            self.console.print("[yellow]Warning: Could not parse JSON, treating as plain text[/yellow]")
            blog_structure = {
                'title': topic,
                'introduction': '',
                'sections': [{'heading': 'Content', 'content': content_text}],
                'conclusion': ''
            }

        return blog_structure

    def _generate_banner_image(self, topic: str, title: str) -> Path:
        """Generate banner image using DALL-E 3"""

        # Create image description
        image_prompt = f"""Create a professional, modern banner image for a blog article titled "{title}".

The image should:
- Be professional and suitable for a technology/AI blog
- Have a clean, modern aesthetic
- Use a color palette of blues, teals, and white
- Be suitable as a header banner
- Include abstract tech/AI imagery (networks, nodes, data flows, circuits, neural patterns)
- NOT include any text or words
- Be minimalist and professional

Style: Modern, clean, tech-focused, professional"""

        # Generate image with DALL-E 3
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1792x1024",  # Wide banner format
            quality="standard",
            n=1
        )

        # Download and save image
        import requests
        from io import BytesIO
        from PIL import Image

        image_url = response.data[0].url
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))

        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = self._sanitize_filename(topic)
        filename = f"{timestamp}_{safe_topic}_banner.png"
        banner_path = self.banner_dir / filename

        img.save(banner_path, 'PNG')

        return banner_path

    def _build_markdown(self, blog_content: Dict, context_info: Dict, banner_path: Optional[Path]) -> str:
        """Build final markdown content"""

        lines = []

        # Title
        lines.append(f"# {blog_content['title']}\n")

        # Banner image (if available)
        if banner_path:
            # Use relative path from output/blogs to output/blogs/banners
            relative_banner = f"banners/{banner_path.name}"
            lines.append(f"![Banner]({relative_banner})\n")

        # Table of contents (if enabled and enough sections)
        if self.include_toc and len(blog_content.get('sections', [])) > 2:
            lines.append("## Table of Contents\n")
            for i, section in enumerate(blog_content['sections'], 1):
                # Create anchor link
                anchor = section['heading'].lower().replace(' ', '-').replace(':', '')
                lines.append(f"{i}. [{section['heading']}](#{anchor})")
            lines.append("")

        # Introduction
        if blog_content.get('introduction'):
            lines.append(blog_content['introduction'])
            lines.append("")

        # Main sections
        for section in blog_content.get('sections', []):
            lines.append(f"## {section['heading']}\n")
            lines.append(section['content'])
            lines.append("")

        # Conclusion
        if blog_content.get('conclusion'):
            lines.append("## Conclusion\n")
            lines.append(blog_content['conclusion'])
            lines.append("")

        # Citations (if enabled)
        if self.include_citations and context_info['num_sources'] > 0:
            lines.append("---\n")
            lines.append("## References\n")
            lines.append("This article was informed by the following sources:\n")
            for source in context_info['sources']:
                # Format: "1. Filename.pdf (Topic: Category)"
                lines.append(f"{source['ref']}. {source['filename']} (Topic: {source['topic']})")
            lines.append("")

        return "\n".join(lines)

    def _save_blog(self, result: Dict, output_path: Path):
        """Save blog to file with metadata"""

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write the markdown content
            f.write(result['content'])

            # Add metadata at the end as comments
            f.write("\n\n---\n")
            f.write("<!-- Metadata\n")
            f.write(f"Topic: {result['topic']}\n")
            f.write(f"Length: {result['length']}\n")
            f.write(f"Word Count: {result['word_count']}\n")
            f.write(f"Sources: {result['num_sources']}\n")
            f.write(f"Generated: {result['timestamp']}\n")
            if result['banner_path']:
                f.write(f"Banner: {result['banner_path']}\n")
            f.write("-->\n")

    def _sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        # Remove special characters, keep alphanumeric and spaces
        safe = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with underscores
        safe = re.sub(r'[\s]+', '_', safe)
        # Limit length
        safe = safe[:50]
        return safe.lower()


if __name__ == "__main__":
    # Test the blog generator
    generator = BlogGenerator()

    result = generator.generate(
        topic="The Future of Multi-Agent AI Systems",
        length="medium",
        create_banner=True
    )

    print(f"\n✓ Generated blog: {result['title']}")
    print(f"  Words: {result['word_count']}")
    print(f"  Sources: {result['num_sources']}")
    if result['banner_path']:
        print(f"  Banner: {result['banner_path']}")
