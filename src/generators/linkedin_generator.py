"""
LinkedIn Post Generator

Generates LinkedIn posts in multiple formats with RAG support.
Supports: text posts, carousel, list posts, story posts
"""

from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json
from openai import OpenAI
from rich.console import Console
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap

import sys
sys.path.append(str(Path(__file__).parent.parent))

from retrieval.retriever import KnowledgeRetriever
from retrieval.context_builder import ContextBuilder

console = Console()


class LinkedInGenerator:
    """Generate LinkedIn posts in various formats"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize LinkedIn generator.

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

        # LinkedIn config
        linkedin_config = self.config.get('linkedin', {})
        self.max_length = linkedin_config.get('max_length', 3000)
        self.include_hashtags = linkedin_config.get('include_hashtags', True)
        self.num_hashtags = linkedin_config.get('num_hashtags', 5)
        self.tone = linkedin_config.get('tone', 'professional')

        # Initialize retriever and context builder
        self.retriever = KnowledgeRetriever(config_path)
        self.context_builder = ContextBuilder()

    def generate(
        self,
        topic: str,
        format_type: str = "text",
        length: str = "medium",
        num_hashtags: int = None,
        custom_hashtags: List[str] = None,
        create_images: bool = False
    ) -> Dict:
        """
        Generate LinkedIn post.

        Args:
            topic: Topic for the post
            format_type: 'text', 'carousel', 'list', or 'story'
            length: 'short', 'medium', or 'long'
            num_hashtags: Number of hashtags (overrides default)
            custom_hashtags: List of custom hashtags to include
            create_images: Whether to generate visual cards for carousel

        Returns:
            Dict with post content and metadata
        """
        # Retrieve relevant knowledge
        chunks = self.retriever.retrieve(topic, top_k=5)
        context_info = self.context_builder.build_context(chunks)

        # Generate based on format
        if format_type == "text":
            result = self._generate_text_post(topic, context_info, length)
        elif format_type == "carousel":
            result = self._generate_carousel_post(topic, context_info, length, create_images)
        elif format_type == "list":
            result = self._generate_list_post(topic, context_info, length)
        elif format_type == "story":
            result = self._generate_story_post(topic, context_info, length)
        else:
            raise ValueError(f"Unknown format: {format_type}. Use 'text', 'carousel', 'list', or 'story'")

        # Generate and add hashtags
        hashtags = self._generate_hashtags(topic, num_hashtags or self.num_hashtags)
        if custom_hashtags:
            hashtags.extend(custom_hashtags)

        result['hashtags'] = hashtags
        result['sources'] = context_info.get('sources', [])

        return result

    def _generate_text_post(self, topic: str, context_info: Dict, length: str) -> Dict:
        """Generate a standard text post"""

        target_words = {"short": 100, "medium": 200, "long": 300}[length]

        system_prompt = self._build_system_prompt(context_info, format_type="text")

        user_prompt = f"""Create a professional and engaging LinkedIn post about: {topic}

Requirements:
- Length: approximately {target_words} words
- Tone: Professional and engaging
- Structure: Hook + Key insights + Call-to-action
- Use the knowledge base context to inform your post
- Start with an attention-grabbing hook
- Include 2-3 key insights or takeaways
- End with a thought-provoking question or call-to-action
- Write in first person or direct address
- Use line breaks for readability

Do NOT include hashtags in the post (they will be added separately)."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        return {
            'format': 'text',
            'content': content,
            'word_count': len(content.split()),
            'char_count': len(content)
        }

    def _generate_carousel_post(
        self,
        topic: str,
        context_info: Dict,
        length: str,
        create_images: bool = False
    ) -> Dict:
        """Generate a carousel post with multiple slides"""

        num_slides = {"short": 5, "medium": 7, "long": 10}[length]

        system_prompt = self._build_system_prompt(context_info, format_type="carousel")

        user_prompt = f"""Create a LinkedIn carousel post about: {topic}

Requirements:
- Number of slides: {num_slides} (including title and CTA slides)
- Tone: Professional and engaging
- Structure each slide with:
  * A compelling headline (max 6 words)
  * 2-3 key points or sentences (max 40 words total)
- Use the knowledge base context to inform your content

Slide breakdown:
- Slide 1: Title slide with compelling headline and subtitle
- Slides 2-{num_slides-1}: Content slides with insights
- Slide {num_slides}: Call-to-action slide

Format your response as JSON with this structure:
{{
  "caption": "Brief caption for the carousel (2-3 sentences)",
  "slides": [
    {{
      "slide_number": 1,
      "headline": "Compelling title",
      "content": ["Subtitle or key point"],
      "visual_suggestion": "Design suggestion (colors, layout, icons)"
    }},
    ...
  ]
}}

Be specific and actionable in the content."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            carousel_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: create simple structure
            carousel_data = {
                "caption": f"Insights about {topic}",
                "slides": [{"slide_number": i+1, "headline": f"Slide {i+1}", "content": [content], "visual_suggestion": "Professional design"}]
            }

        result = {
            'format': 'carousel',
            'caption': carousel_data.get('caption', ''),
            'slides': carousel_data.get('slides', []),
            'num_slides': len(carousel_data.get('slides', []))
        }

        # Generate images if requested
        if create_images:
            image_paths = self._create_carousel_images(carousel_data.get('slides', []), topic)
            result['image_paths'] = image_paths

        return result

    def _generate_list_post(self, topic: str, context_info: Dict, length: str) -> Dict:
        """Generate a numbered list post"""

        num_items = {"short": 5, "medium": 7, "long": 10}[length]

        system_prompt = self._build_system_prompt(context_info, format_type="list")

        user_prompt = f"""Create a LinkedIn list post about: {topic}

Requirements:
- Create a numbered list with {num_items} key points
- Tone: Professional and engaging
- Format: Introduction + Numbered list + Conclusion
- Each list item should be concise (1-2 sentences)
- Use the knowledge base context to inform your points
- Start with a brief introduction (2-3 sentences)
- End with a conclusion or call-to-action

Structure:
[Brief intro]

1. [First key point]
2. [Second key point]
...

[Brief conclusion]

Do NOT include hashtags (they will be added separately)."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        return {
            'format': 'list',
            'content': content,
            'num_items': num_items,
            'word_count': len(content.split())
        }

    def _generate_story_post(self, topic: str, context_info: Dict, length: str) -> Dict:
        """Generate a narrative/story format post"""

        target_words = {"short": 150, "medium": 250, "long": 350}[length]

        system_prompt = self._build_system_prompt(context_info, format_type="story")

        user_prompt = f"""Create a LinkedIn story-format post about: {topic}

Requirements:
- Length: approximately {target_words} words
- Tone: Professional, engaging, and narrative-driven
- Structure: Problem → Solution → Impact
- Use the knowledge base context to inform your story
- Write in a narrative style with a clear arc
- Include specific examples or scenarios
- Make it relatable and actionable
- End with a powerful insight or lesson

Story structure:
1. Problem/Challenge: What's the issue?
2. Solution/Approach: How was it addressed?
3. Impact/Outcome: What changed?

Do NOT include hashtags (they will be added separately)."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )

        content = response.choices[0].message.content

        return {
            'format': 'story',
            'content': content,
            'word_count': len(content.split())
        }

    def _generate_hashtags(self, topic: str, num_hashtags: int) -> List[str]:
        """Generate relevant hashtags"""

        prompt = f"""Generate {num_hashtags} highly relevant LinkedIn hashtags for a post about: {topic}

Requirements:
- Mix of popular and niche hashtags
- Relevant to AI, technology, and business
- Professional and appropriate for LinkedIn
- Format: #Hashtag (include the # symbol)
- One hashtag per line

Return ONLY the hashtags, nothing else."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a LinkedIn marketing expert. Generate relevant hashtags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )

        hashtags_text = response.choices[0].message.content.strip()
        hashtags = [line.strip() for line in hashtags_text.split('\n') if line.strip().startswith('#')]

        return hashtags[:num_hashtags]

    def _build_system_prompt(self, context_info: Dict, format_type: str) -> str:
        """Build system prompt with knowledge base context"""

        if not context_info['has_relevant_info']:
            return f"""You are a professional LinkedIn content creator specializing in AI and technology.

Create engaging, professional LinkedIn content in {format_type} format.

Tone: Professional and engaging
Focus: AI, Agentic systems, and technology trends
Style: Clear, actionable, and valuable to professionals"""

        return f"""You are a professional LinkedIn content creator specializing in AI and technology.

You have access to relevant knowledge base content with {context_info['num_chunks']} excerpts.

{context_info['context']}

{context_info['source_references']}

Create engaging, professional LinkedIn content in {format_type} format.

IMPORTANT:
- Use the knowledge base context as your PRIMARY source
- Synthesize insights from the provided excerpts
- Add professional commentary and context
- Make it engaging and valuable for LinkedIn professionals
- Do NOT copy text verbatim; synthesize and add value

Tone: Professional and engaging
Style: Clear, actionable, and valuable to professionals"""

    def _create_carousel_images(self, slides: List[Dict], topic: str) -> List[str]:
        """Create carousel card images using Pillow"""

        output_dir = Path(self.config['output']['base_directory']) / 'linkedin' / 'carousel'
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_paths = []

        # LinkedIn carousel image size (1080x1080 recommended)
        img_width, img_height = 1080, 1080

        # Color scheme (professional LinkedIn colors)
        colors = {
            'background': '#FFFFFF',
            'primary': '#0A66C2',  # LinkedIn blue
            'secondary': '#E7F3FF',
            'text': '#000000',
            'accent': '#F3F6F8'
        }

        for i, slide in enumerate(slides, 1):
            # Create image
            img = Image.new('RGB', (img_width, img_height), colors['background'])
            draw = ImageDraw.Draw(img)

            # Try to load fonts, fallback to default if not available
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
                content_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 45)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
            except:
                title_font = ImageFont.load_default()
                content_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

            # Add colored header bar
            draw.rectangle([0, 0, img_width, 150], fill=colors['primary'])

            # Add slide number
            draw.text((50, 50), f"{i}/{len(slides)}", fill='#FFFFFF', font=small_font)

            # Add headline
            headline = slide.get('headline', f'Slide {i}')

            # Wrap headline text
            max_chars_per_line = 30
            wrapped_headline = textwrap.wrap(headline, width=max_chars_per_line)

            y_offset = 250
            for line in wrapped_headline:
                draw.text((60, y_offset), line, fill=colors['text'], font=title_font)
                y_offset += 100

            # Add content
            content = slide.get('content', [])
            if isinstance(content, list):
                content_text = '\n'.join(f"• {item}" for item in content)
            else:
                content_text = str(content)

            # Wrap content text
            wrapped_content = textwrap.wrap(content_text, width=35)

            y_offset += 80
            for line in wrapped_content[:8]:  # Max 8 lines to fit
                draw.text((60, y_offset), line, fill=colors['text'], font=content_font)
                y_offset += 60

            # Add footer with topic
            draw.rectangle([0, img_height-100, img_width, img_height], fill=colors['accent'])
            footer_text = topic[:50] + '...' if len(topic) > 50 else topic
            draw.text((60, img_height-70), footer_text, fill=colors['text'], font=small_font)

            # Save image
            filename = f"{timestamp}_slide_{i:02d}.png"
            filepath = output_dir / filename
            img.save(filepath, 'PNG', quality=95)
            image_paths.append(str(filepath))

            self.console.print(f"[green]Created:[/green] {filepath.name}")

        return image_paths

    def format_output(self, result: Dict) -> str:
        """Format the result for display"""

        output = []

        if result['format'] == 'text':
            output.append("=== LinkedIn Text Post ===\n")
            output.append(result['content'])
            output.append(f"\n\n{' '.join(result['hashtags'])}")
            output.append(f"\n\n--- Metadata ---")
            output.append(f"Words: {result['word_count']}")
            output.append(f"Characters: {result['char_count']}")

        elif result['format'] == 'carousel':
            output.append("=== LinkedIn Carousel Post ===\n")
            output.append(f"Caption: {result['caption']}\n")
            output.append(f"{' '.join(result['hashtags'])}\n")
            output.append(f"\n--- {result['num_slides']} Slides ---\n")

            for slide in result['slides']:
                output.append(f"\n▸ Slide {slide.get('slide_number', '?')}")
                output.append(f"  Headline: {slide.get('headline', '')}")
                if isinstance(slide.get('content'), list):
                    for item in slide['content']:
                        output.append(f"  • {item}")
                else:
                    output.append(f"  {slide.get('content', '')}")
                if 'visual_suggestion' in slide:
                    output.append(f"  [Design: {slide['visual_suggestion']}]")

            if 'image_paths' in result:
                output.append(f"\n\n--- Generated Images ---")
                for path in result['image_paths']:
                    output.append(f"  {path}")

        elif result['format'] == 'list':
            output.append("=== LinkedIn List Post ===\n")
            output.append(result['content'])
            output.append(f"\n\n{' '.join(result['hashtags'])}")
            output.append(f"\n\n--- Metadata ---")
            output.append(f"Words: {result['word_count']}")

        elif result['format'] == 'story':
            output.append("=== LinkedIn Story Post ===\n")
            output.append(result['content'])
            output.append(f"\n\n{' '.join(result['hashtags'])}")
            output.append(f"\n\n--- Metadata ---")
            output.append(f"Words: {result['word_count']}")

        # Add sources
        if result['sources']:
            output.append(f"\n\n--- Knowledge Base Sources ---")
            for src in result['sources']:
                output.append(f"  [{src['ref']}] {src['filename']}")

        return '\n'.join(output)
