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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show source references")
):
    """
    Interactive Q&A chatbot using the AI and Agentic knowledge base

    Examples:
      python src/main.py chat "What are the key principles of agentic AI?"
      python src/main.py chat --verbose
    """
    console.print(Panel.fit(
        "[bold cyan]Q&A Chatbot[/bold cyan]\n"
        "Ask questions about AI and Agents",
        border_style="cyan"
    ))

    if question:
        console.print(f"\n[yellow]Question:[/yellow] {question}")
        console.print("\n[dim]Processing... (Knowledge base not yet initialized)[/dim]")
        console.print("\n[red]Note:[/red] Q&A agent not yet implemented. Coming in Phase 3.")
    else:
        console.print("\n[yellow]Interactive mode[/yellow]")
        console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")

        while True:
            try:
                user_input = typer.prompt("You")
                if user_input.lower() in ['exit', 'quit']:
                    console.print("\n[cyan]Goodbye![/cyan]")
                    break

                console.print("\n[dim]Processing... (Knowledge base not yet initialized)[/dim]")
                console.print("[red]Note:[/red] Q&A agent not yet implemented. Coming in Phase 3.\n")
            except (KeyboardInterrupt, EOFError):
                console.print("\n\n[cyan]Goodbye![/cyan]")
                break


@generate_app.command("linkedin")
def generate_linkedin(
    topic: str = typer.Argument(..., help="Topic for the LinkedIn post"),
    tone: str = typer.Option("professional", help="Tone: professional, casual, inspirational"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path")
):
    """
    Generate a professional LinkedIn post

    Examples:
      python src/main.py generate linkedin "The future of agentic AI"
      python src/main.py generate linkedin "Multi-agent systems" --tone casual
    """
    console.print(Panel.fit(
        "[bold green]LinkedIn Post Generator[/bold green]\n"
        f"Topic: {topic}",
        border_style="green"
    ))

    console.print("\n[dim]Generating LinkedIn post... (Generator not yet implemented)[/dim]")
    console.print("[red]Note:[/red] LinkedIn generator not yet implemented. Coming in Phase 4.\n")


@generate_app.command("blog")
def generate_blog(
    topic: str = typer.Argument(..., help="Topic for the blog post"),
    length: str = typer.Option("medium", help="Length: short, medium, long"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path")
):
    """
    Generate a detailed blog article

    Examples:
      python src/main.py generate blog "Understanding RAG systems"
      python src/main.py generate blog "LangChain agents" --length long
    """
    console.print(Panel.fit(
        "[bold magenta]Blog Generator[/bold magenta]\n"
        f"Topic: {topic}",
        border_style="magenta"
    ))

    console.print("\n[dim]Generating blog post... (Generator not yet implemented)[/dim]")
    console.print("[red]Note:[/red] Blog generator not yet implemented. Coming in Phase 5.\n")


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

        console.print("\n[yellow]Implementation Status:[/yellow]")
        console.print("  - Phase 1: Project Setup [green]✓ Complete[/green]")
        console.print("  - Phase 2: Knowledge Base Ingestion [yellow]⧖ Pending[/yellow]")
        console.print("  - Phase 3: Q&A Chatbot [yellow]⧖ Pending[/yellow]")
        console.print("  - Phase 4: LinkedIn Generator [yellow]⧖ Pending[/yellow]")
        console.print("  - Phase 5: Blog Generator [yellow]⧖ Pending[/yellow]")
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
