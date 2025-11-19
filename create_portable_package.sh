#!/bin/bash

# Create Portable Package for AI Agentic Companion
# This script creates a clean package without machine-specific files

echo "=================================="
echo "Creating Portable Package"
echo "=================================="
echo ""

PACKAGE_NAME="ai-agentic-companion-v1.0.0"
PACKAGE_DIR="portable_package"

# Create package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME"

echo "📦 Copying project files..."

# Copy essential files and directories
rsync -av \
    --exclude-from='.packageignore' \
    --exclude='portable_package' \
    --exclude='create_portable_package.sh' \
    ./ "$PACKAGE_DIR/$PACKAGE_NAME/"

# Create secrets directory placeholder
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/config/secrets"
cat > "$PACKAGE_DIR/$PACKAGE_NAME/config/secrets/README.txt" << 'EOF'
IMPORTANT: Create config.json in this directory

File: config/secrets/config.json
Content:
{
  "OPENAI_API_KEY": "your-openai-api-key-here",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}

Get your API key from: https://platform.openai.com/api-keys
EOF

# Create data directories
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/data/vector_db"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/linkedin"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/blogs"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/podcasts"

# Create deployment guide
cat > "$PACKAGE_DIR/$PACKAGE_NAME/DEPLOYMENT.md" << 'EOF'
# Deployment Guide

## Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- OpenAI API key
- PDF corpus (or update config to point to your PDFs)

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Create `config/secrets/config.json`:
```json
{
  "OPENAI_API_KEY": "sk-...",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}
```

### 4. Configure Corpus Path
Edit `config/config.yaml` and update the corpus path:
```yaml
corpus:
  path: "/path/to/your/PDFs"
```

### 5. Ingest Knowledge Base
```bash
python src/main.py ingest
```

This will:
- Process all PDFs in your corpus
- Generate embeddings
- Store in ChromaDB vector database
- Takes ~10-30 minutes depending on corpus size

### 6. Launch Web UI
```bash
./run_web_ui.sh
```

Access at: http://localhost:8000

## Alternative: CLI Usage

```bash
# Q&A Chatbot
python src/main.py chat

# Generate LinkedIn post
python src/main.py generate linkedin "Your topic"

# Generate blog article
python src/main.py generate blog "Your topic"

# Generate podcast
python src/main.py generate podcast "Your topic"
```

## Troubleshooting

### "No module named 'xxx'"
Run: `pip install -r requirements.txt`

### "FileNotFoundError: config/config.yaml"
Make sure you're in the project root directory

### "No such file or directory: config/secrets/config.json"
Create the secrets file with your API key

### Port 8000 already in use
Edit `src/web/app.py` and change the port number

## Notes

- First ingestion takes time depending on corpus size
- Vector database is stored in `data/vector_db/`
- Generated content saved to `output/` directory
- See README.md for full documentation
EOF

# Create archive
echo ""
echo "📦 Creating archive..."
cd "$PACKAGE_DIR"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
cd ..

# Show results
echo ""
echo "=================================="
echo "✅ Package created successfully!"
echo "=================================="
echo ""
echo "📦 Package: portable_package/$PACKAGE_NAME.tar.gz"
echo "📏 Size: $(du -h portable_package/$PACKAGE_NAME.tar.gz | cut -f1)"
echo ""
echo "To deploy on another computer:"
echo "1. Copy $PACKAGE_NAME.tar.gz to the new machine"
echo "2. Extract: tar -xzf $PACKAGE_NAME.tar.gz"
echo "3. Follow instructions in DEPLOYMENT.md"
echo ""
