# AI Agentic Companion

An intelligent AI assistant powered by a comprehensive knowledge base of AI and Agentic content. Provides Q&A chatbot capabilities, professional content generation (LinkedIn posts and blog articles), and podcast creation.

## Overview

This project creates an agentic AI system that:

1. **Q&A Chatbot**: Answer questions using a 944MB corpus of AI and Agent PDFs with RAG (Retrieval-Augmented Generation)
2. **LinkedIn Post Generator**: Create professional, engaging LinkedIn posts on AI topics
3. **Blog Generator**: Generate detailed blog articles with citations and structure
4. **Podcast Creator**: Generate multi-speaker podcast episodes as MP3 files

## Knowledge Base

The AI is trained on a comprehensive corpus of 153 PDFs covering:

- **Source**: `/Users/pranav/Downloads/AI and Agentic`
- **Size**: ~944MB of content
- **Topics**:
  - Agents & Multi-Agent Systems
  - Architecture & Design Patterns
  - Automation & Workflows
  - Consulting Strategy
  - Data & Analytics
  - Gen AI & LLMs
  - MCP (Model Context Protocol)
  - Security
  - Vibe Coding
  - Hiring & Talent

## Project Structure

```
ai-agentic-companion/
├── src/
│   ├── main.py              # CLI entry point
│   ├── agents/              # Agent implementations
│   │   ├── qa_agent.py
│   │   ├── content_agent.py
│   │   └── podcast_agent.py
│   ├── knowledge/           # Knowledge base processing
│   │   ├── pdf_processor.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   └── vector_store.py
│   ├── retrieval/           # Search & retrieval logic
│   ├── generators/          # Content generators
│   │   ├── linkedin_generator.py
│   │   ├── blog_generator.py
│   │   └── podcast_generator.py
│   └── audio/               # TTS and audio processing
├── config/
│   ├── config.yaml          # Main configuration
│   ├── prompts/             # Agent prompt templates
│   └── secrets/             # API keys (gitignored)
├── data/
│   ├── vector_db/           # ChromaDB storage
│   └── cache/               # Temporary files
├── output/
│   ├── blogs/               # Generated blog posts
│   ├── linkedin/            # Generated LinkedIn posts
│   └── podcasts/            # Generated podcast MP3s
└── tests/                   # Unit tests
```

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/pranavjh/ai-agentic-companion.git
cd ai-agentic-companion

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The `config/secrets/config.json` file should contain:

```json
{
  "OPENAI_API_KEY": "sk-...",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}
```

## Usage

**Important:** Always activate the virtual environment first:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Q&A Chatbot

```bash
# Ask a single question
python src/main.py chat "What are the key principles of agentic AI?"

# Interactive mode
python src/main.py chat

# Show source references
python src/main.py chat "Explain RAG systems" --verbose
```

### Generate LinkedIn Post

```bash
# Generate a professional LinkedIn post
python src/main.py generate linkedin "The future of agentic AI"

# Custom tone
python src/main.py generate linkedin "Multi-agent systems" --tone casual

# Save to file
python src/main.py generate linkedin "AI trends" -o my_post.txt
```

### Generate Blog Article

```bash
# Generate a blog post
python src/main.py generate blog "Understanding RAG systems"

# Custom length
python src/main.py generate blog "LangChain agents" --length long

# Save to file
python src/main.py generate blog "AI architecture" -o output/my_blog.md
```

### Generate Podcast

```bash
# Generate a 10-minute podcast episode
python src/main.py generate podcast "The evolution of LLMs"

# Custom duration
python src/main.py generate podcast "Agentic workflows" --duration 15

# Save to specific location
python src/main.py generate podcast "AI security" -o my_podcast.mp3
```

### Check Status

```bash
# View project status and configuration
python src/main.py status

# View version
python src/main.py version
```

## Features

### Core Features
- 🤖 Multi-agent system with specialized agents for different tasks
- 📚 RAG-powered Q&A with 944MB knowledge base
- 🔍 Hybrid search (semantic + keyword) with re-ranking
- ✍️ Professional content generation (LinkedIn, blogs)
- 🎙️ Podcast generation with two-speaker dialogue
- 🎤 High-quality text-to-speech (OpenAI TTS-1-HD)
- 💾 Vector database with ChromaDB for efficient retrieval
- 📊 Citation and source tracking
- ⚙️ Configurable parameters for all generators

### Planned Features
- [ ] Web interface for easier interaction
- [ ] Custom voice selection for podcasts
- [ ] Multi-language support
- [ ] Batch content generation
- [ ] Integration with social media APIs
- [ ] Custom knowledge base upload
- [ ] Advanced analytics and insights

## Technology Stack

- **LLM Framework**: LangChain for agent orchestration
- **LLM**: OpenAI GPT-4o (latest model)
- **Embeddings**: text-embedding-3-large for semantic search
- **Vector Database**: ChromaDB for local storage
- **PDF Processing**: PyPDF2 and pdfplumber
- **Search**: Hybrid search with BM25 keyword matching
- **TTS**: OpenAI TTS-1-HD for podcast audio
- **Audio**: pydub for audio processing
- **CLI**: Typer with Rich for beautiful terminal interface

## Development Status

- [x] Phase 1: Project Setup & Infrastructure ✅
- [ ] Phase 2: Knowledge Base Ingestion (PDF processing, embeddings)
- [ ] Phase 3: RAG System & Q&A Chatbot
- [ ] Phase 4: LinkedIn Post Generator
- [ ] Phase 5: Blog Generator
- [ ] Phase 6: Podcast Generator
- [ ] Phase 7: Agent Orchestration & Advanced Features
- [ ] Phase 8: Testing & Optimization

## License

MIT

## Author

Pranav JH (@pranavjh)

## Notes

- Uses virtual environment to avoid dependency conflicts
- API keys stored in `config/secrets/` (gitignored)
- Vector database stored locally in `data/vector_db/`
- All generated content saved to `output/` directory
