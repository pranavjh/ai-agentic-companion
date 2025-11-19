# Changelog

All notable changes to AI Agentic Companion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-18

### Added

#### Phase 1: Project Setup
- Initial project structure and repository
- Virtual environment setup
- Configuration system with YAML and secrets management
- Git repository and GitHub integration

#### Phase 2: Knowledge Base Ingestion
- PDF processing with text extraction (no OCR)
- Document chunking (1500 tokens, 200 overlap)
- OpenAI embeddings (text-embedding-3-large)
- ChromaDB vector database with persistent storage
- Hash-based incremental update system
- Successfully processed 136 PDFs (2,168 chunks) from 944MB corpus

#### Phase 3: Q&A Chatbot
- RAG-powered question answering
- Conversation memory (configurable, default 10 messages)
- Source citations from knowledge base
- LLM verification and enhancement of answers
- CLI interface with interactive and single-question modes
- Clear command to reset conversation history

#### Phase 4: LinkedIn Post Generator
- Four post formats: text, carousel, list, story
- Professional and engaging tone
- Auto-generated hashtags with custom hashtag support
- Visual carousel card generation (1080x1080 PNG with Pillow)
- Knowledge base integration for accurate content
- CLI interface with comprehensive options

#### Phase 5: Blog Article Generator
- Three length options: short (~500), medium (~1000), long (~1500-2000 words)
- DALL-E 3 banner image generation (1792x1024)
- Well-structured articles with intro, sections, conclusion
- Automatic table of contents for multi-section articles
- Knowledge base integration with source citations
- Markdown output format
- CLI interface with banner toggle

#### Phase 6: Podcast Episode Generator
- Two formats: monologue (single speaker) and conversation (Q&A style)
- OpenAI TTS integration (tts-1-hd)
- Six voice options: alloy, echo, fable, onyx, nova, shimmer
- Configurable length (1-60 minutes)
- Includes intro, main content, and outro segments
- Always generates transcript, optional MP3 audio
- Knowledge base integration for content
- CLI interface with voice selection

#### Phase 7: Web UI
- Modern, responsive web interface with Bootstrap 5
- Tabbed navigation for all features
- Real-time content generation with loading indicators
- Session-based chat conversations
- File download functionality for all generated content
- Beautiful purple gradient design
- Status indicator showing knowledge base readiness
- Runs on localhost:8000 (avoiding macOS port conflicts)

### Technical Features
- LangChain for agent orchestration
- OpenAI GPT-4o for text generation
- Hybrid search (semantic + keyword)
- ChromaDB for vector storage
- Flask web server
- Typer CLI with Rich terminal UI
- Professional error handling and validation

### Fixed
- Working directory issue in web UI
- Port conflict with macOS ControlCenter (moved from 5000 to 8000)
- Reference formatting in blog citations
- Path resolution for config files

[1.0.0]: https://github.com/pranavjh/ai-agentic-companion/releases/tag/v1.0.0
