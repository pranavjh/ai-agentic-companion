#!/usr/bin/env python3
"""
AI Agentic Companion - Main CLI Entry Point

Commands:
  - chat: Interactive Q&A chatbot
  - generate linkedin: Create LinkedIn posts
  - generate blog: Create blog articles
  - generate podcast: Create podcast episodes
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path
from datetime import datetime
import yaml
import json

app = typer.Typer(
    name="ai-companion",
    help="AI Agentic Companion - Your AI assistant for Q&A and content generation",
    add_completion=False
)

generate_app = typer.Typer(help="Generate content (LinkedIn, blog, podcast)")
app.add_typer(generate_app, name="generate")

console = Console()

# Load configuration
def load_config():
    """Load configuration from config.yaml and secrets"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    secrets_path = Path(__file__).parent.parent / "config" / "secrets" / "config.json"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if secrets_path.exists():
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
            config['secrets'] = secrets

    return config


@app.command()
def chat(
    question: str = typer.Argument(None, help="Question to ask (interactive mode if not provided)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show source references and retrieval details")
):
    """
    Interactive Q&A chatbot using the AI and Agentic knowledge base

    Features:
    - Retrieves relevant information from your knowledge base
    - Enhances answers with latest information from GPT-4o
    - Maintains conversation continuity (last 10 messages)
    - Provides source citations

    Examples:
      python src/main.py chat "What are the key principles of agentic AI?"
      python src/main.py chat --verbose
      python src/main.py chat  # Interactive mode
    """
    from agents.qa_agent import QAAgent
    from retrieval.context_builder import ContextBuilder

    console.print(Panel.fit(
        "[bold cyan]Q&A Chatbot[/bold cyan]\n"
        "Ask questions about AI and Agents\n"
        "[dim]Knowledge base ready with 2,168 chunks from 136 documents[/dim]",
        border_style="cyan"
    ))

    try:
        # Initialize Q&A agent
        agent = QAAgent()
        context_builder = ContextBuilder()

        if question:
            # Single question mode
            console.print(f"\n[yellow]Question:[/yellow] {question}\n")

            # Get answer
            with console.status("[cyan]Thinking...[/cyan]"):
                result = agent.answer(question, verbose=verbose)

            # Display answer
            console.print(f"[green]Answer:[/green]\n{result['answer']}\n")

            # Display sources
            if result['sources'] or not result['has_kb_sources']:
                sources_display = context_builder.format_sources_for_display(
                    result['sources'],
                    include_general=True
                )
                console.print(sources_display)

        else:
            # Interactive mode
            console.print("\n[yellow]Interactive mode[/yellow]")
            console.print("[dim]Type 'exit', 'quit', or 'clear' (to reset conversation)[/dim]\n")

            while True:
                try:
                    user_input = typer.prompt("\n[bold cyan]You[/bold cyan]")

                    if user_input.lower() in ['exit', 'quit']:
                        console.print(f"\n[cyan]Goodbye! ({agent.get_conversation_summary()})[/cyan]")
                        break

                    if user_input.lower() == 'clear':
                        agent.clear_history()
                        console.print("[yellow]Conversation history cleared[/yellow]")
                        continue

                    if not user_input.strip():
                        continue

                    # Get answer
                    with console.status("[cyan]Thinking...[/cyan]"):
                        result = agent.answer(user_input, verbose=verbose)

                    # Display answer
                    console.print(f"\n[bold green]Assistant:[/bold green]\n{result['answer']}")

                    # Display sources
                    if result['sources'] or not result['has_kb_sources']:
                        sources_display = context_builder.format_sources_for_display(
                            result['sources'],
                            include_general=True
                        )
                        console.print(sources_display)

                    # Show conversation stats if verbose
                    if verbose:
                        console.print(f"\n[dim]Conversation: {result['conversation_length']} messages | Retrieved: {result['num_chunks']} chunks[/dim]")

                except (KeyboardInterrupt, EOFError):
                    console.print(f"\n\n[cyan]Goodbye! ({agent.get_conversation_summary()})[/cyan]")
                    break

    except Exception as e:
        console.print(f"\n[red]Error initializing Q&A agent:[/red] {e}")
        console.print("[yellow]Make sure you've run 'python src/main.py ingest' first[/yellow]")
        raise typer.Exit(code=1)


@generate_app.command("linkedin")
def generate_linkedin(
    topic: str = typer.Argument(..., help="Topic for the LinkedIn post"),
    format_type: str = typer.Option("text", "--format", "-f", help="Format: text, carousel, list, story"),
    length: str = typer.Option("medium", "--length", "-l", help="Length: short, medium, long"),
    num_hashtags: int = typer.Option(5, "--hashtags", "-h", help="Number of hashtags to generate"),
    custom_hashtags: str = typer.Option(None, "--custom", "-c", help="Custom hashtags (comma-separated)"),
    create_images: bool = typer.Option(False, "--create-images", "-i", help="Create visual carousel cards (carousel format only)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path")
):
    """
    Generate professional LinkedIn posts in multiple formats

    Formats:
      - text: Standard text post with hashtags
      - carousel: Multi-slide carousel (with optional image generation)
      - list: Numbered list format
      - story: Narrative/storytelling format

    Features:
      - Uses knowledge base for accurate content
      - Auto-generates relevant hashtags
      - Professional and engaging tone
      - Supports custom hashtags

    Examples:
      python src/main.py generate linkedin "The future of agentic AI"
      python src/main.py generate linkedin "RAG systems" --format carousel --create-images
      python src/main.py generate linkedin "Multi-agent patterns" --format list --length long
      python src/main.py generate linkedin "AI adoption" --custom "#AI,#Innovation" -o my_post.txt
    """
    from generators.linkedin_generator import LinkedInGenerator

    console.print(Panel.fit(
        "[bold green]LinkedIn Post Generator[/bold green]\n"
        f"Topic: {topic}\n"
        f"Format: {format_type} | Length: {length}",
        border_style="green"
    ))

    try:
        # Parse custom hashtags
        custom_tags = None
        if custom_hashtags:
            custom_tags = [tag.strip() if tag.startswith('#') else f'#{tag.strip()}'
                          for tag in custom_hashtags.split(',')]

        # Initialize generator
        generator = LinkedInGenerator()

        # Generate post
        with console.status(f"[green]Generating {format_type} post...[/green]"):
            result = generator.generate(
                topic=topic,
                format_type=format_type,
                length=length,
                num_hashtags=num_hashtags,
                custom_hashtags=custom_tags,
                create_images=create_images
            )

        # Display result
        console.print("\n")
        formatted_output = generator.format_output(result)
        console.print(formatted_output)

        # Save to file if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                f.write(formatted_output)
            console.print(f"\n[green]✓ Saved to:[/green] {output}")
        else:
            # Auto-save to output directory
            output_dir = Path(generator.config['output']['linkedin']['directory'])
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{topic[:30].replace(' ', '_')}_{format_type}.txt"
            filepath = output_dir / filename

            with open(filepath, 'w') as f:
                f.write(formatted_output)
            console.print(f"\n[green]✓ Saved to:[/green] {filepath}")

    except Exception as e:
        console.print(f"\n[red]Error generating LinkedIn post:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


@generate_app.command("blog")
def generate_blog(
    topic: str = typer.Argument(..., help="Topic for the blog article"),
    length: str = typer.Option("medium", "--length", "-l", help="Length: short (~500 words), medium (~1000 words), long (~1500-2000 words)"),
    create_banner: bool = typer.Option(True, "--banner/--no-banner", "-b", help="Generate banner image with DALL-E 3"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (.md)")
):
    """
    Generate professional blog articles with banner images

    Features:
      - Uses knowledge base for accurate, well-researched content
      - Professional, informative tone
      - Well-structured with sections and conclusion
      - Optional table of contents
      - DALL-E 3 generated banner images
      - Source citations from knowledge base

    Lengths:
      - short: ~500 words, 3 sections
      - medium: ~1000 words, 5 sections
      - long: ~1500-2000 words, 7 sections

    Examples:
      python src/main.py generate blog "Understanding RAG systems"
      python src/main.py generate blog "Multi-agent AI architectures" --length long
      python src/main.py generate blog "The future of agentic AI" --no-banner
      python src/main.py generate blog "LangChain deep dive" -o my_blog.md
    """
    from generators.blog_generator import BlogGenerator

    console.print(Panel.fit(
        "[bold magenta]Blog Generator[/bold magenta]\n"
        f"Topic: {topic}\n"
        f"Length: {length} | Banner: {'Yes' if create_banner else 'No'}",
        border_style="magenta"
    ))

    try:
        # Initialize generator
        generator = BlogGenerator()

        # Generate blog
        result = generator.generate(
            topic=topic,
            length=length,
            create_banner=create_banner,
            output_path=output
        )

        # Display preview
        console.print(f"\n[bold green]✓ Blog Generated Successfully[/bold green]")
        console.print(f"\n[cyan]Title:[/cyan] {result['title']}")
        console.print(f"[cyan]Word Count:[/cyan] {result['word_count']}")
        console.print(f"[cyan]Sources:[/cyan] {result['num_sources']} knowledge base sources")
        if result['banner_path']:
            console.print(f"[cyan]Banner:[/cyan] {result['banner_path']}")

    except Exception as e:
        console.print(f"\n[red]Error generating blog:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


@generate_app.command("podcast")
def generate_podcast(
    topic: str = typer.Argument(..., help="Topic for the podcast episode"),
    duration: int = typer.Option(10, help="Target duration in minutes"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (.mp3)")
):
    """
    Generate a podcast episode with two speakers

    Examples:
      python src/main.py generate podcast "The evolution of LLMs"
      python src/main.py generate podcast "Agentic workflows" --duration 15
    """
    console.print(Panel.fit(
        "[bold blue]Podcast Generator[/bold blue]\n"
        f"Topic: {topic}\n"
        f"Duration: ~{duration} minutes",
        border_style="blue"
    ))

    console.print("\n[dim]Generating podcast script... (Generator not yet implemented)[/dim]")
    console.print("[red]Note:[/red] Podcast generator not yet implemented. Coming in Phase 6.\n")


@app.command()
def ingest(
    force: bool = typer.Option(False, "--force", "-f", help="Force reindex all files (ignore processed status)"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Number of files to process per batch")
):
    """
    Ingest PDF corpus into vector database

    This command processes PDFs from the configured corpus path, extracts text,
    chunks it, generates embeddings, and stores in ChromaDB.

    Features:
    - Incremental updates (only processes new/modified files)
    - Hash-based change detection
    - Progress tracking with rich output

    Examples:
      python src/main.py ingest
      python src/main.py ingest --force  # Reprocess all files
    """
    from knowledge.ingest import KnowledgeBaseIngester

    try:
        ingester = KnowledgeBaseIngester()
        ingester.ingest_corpus(force_reindex=force, batch_size=batch_size)
    except Exception as e:
        console.print(f"\n[red]Error during ingestion:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show project status and configuration"""
    console.print(Panel.fit(
        "[bold cyan]AI Agentic Companion - Project Status[/bold cyan]",
        border_style="cyan"
    ))

    try:
        config = load_config()

        console.print("\n[green]✓[/green] Configuration loaded successfully")
        console.print(f"  - LLM Model: {config['models']['llm']}")
        console.print(f"  - Embedding Model: {config['models']['embedding']}")
        console.print(f"  - Corpus Path: {config['corpus']['path']}")

        corpus_path = Path(config['corpus']['path'])
        if corpus_path.exists():
            console.print(f"\n[green]✓[/green] Corpus directory found")
        else:
            console.print(f"\n[red]✗[/red] Corpus directory not found at {corpus_path}")

        # Check if vector DB exists
        vector_db_path = Path(config['vector_db']['persist_directory'])
        if vector_db_path.exists():
            from knowledge.vector_store import VectorStoreManager
            vs = VectorStoreManager(
                persist_directory=str(vector_db_path),
                collection_name=config['vector_db']['collection_name']
            )
            stats = vs.get_stats()
            console.print(f"[green]✓[/green] Vector DB found ({stats['total_chunks']} chunks, {stats['processed_files']} files)")
        else:
            console.print(f"[yellow]⧖[/yellow] Vector DB not yet created")

        console.print("\n[yellow]Implementation Status:[/yellow]")
        console.print("  - Phase 1: Project Setup [green]✓ Complete[/green]")
        console.print("  - Phase 2: Knowledge Base Ingestion [green]✓ Complete[/green]")
        console.print("  - Phase 3: Q&A Chatbot [green]✓ Complete[/green]")
        console.print("  - Phase 4: LinkedIn Generator [green]✓ Complete[/green]")
        console.print("  - Phase 5: Blog Generator [green]✓ Complete[/green]")
        console.print("  - Phase 6: Podcast Generator [yellow]⧖ Pending[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Error loading configuration:[/red] {e}")


@app.command()
def version():
    """Show version information"""
    from . import __version__, __author__
    console.print(f"\n[cyan]AI Agentic Companion[/cyan] v{__version__}")
    console.print(f"Author: {__author__}\n")


if __name__ == "__main__":
    app()
