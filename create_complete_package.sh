#!/bin/bash

# Create Complete Package with Vector Database
# This package is READY TO USE - no PDFs or ingestion needed!

echo "=========================================="
echo "Creating Complete Deployment Package"
echo "=========================================="
echo ""
echo "This package includes:"
echo "  ✓ All source code"
echo "  ✓ Processed vector database"
echo "  ✓ Configuration files"
echo ""
echo "User will NOT need:"
echo "  ✗ Original PDF corpus"
echo "  ✗ To run ingestion"
echo ""
echo "=========================================="
echo ""

PACKAGE_NAME="ai-agentic-companion-complete-v1.0.0"
PACKAGE_DIR="portable_package"

# Create package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME"

echo "📦 Copying project files..."

# Copy everything except machine-specific files
rsync -av \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='output/' \
    --exclude='config/secrets/' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='portable_package/' \
    --exclude='*.sh' \
    ./ "$PACKAGE_DIR/$PACKAGE_NAME/"

# Verify vector DB exists
if [ ! -d "data/vector_db" ]; then
    echo ""
    echo "⚠️  WARNING: Vector database not found!"
    echo "   Run 'python src/main.py ingest' first"
    exit 1
fi

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

# Create output directories
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/linkedin"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/blogs"
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/output/podcasts"

# Create quick start guide
cat > "$PACKAGE_DIR/$PACKAGE_NAME/QUICK_START.md" << 'EOF'
# Quick Start - Complete Package

This package includes the processed knowledge base!
NO PDF corpus or ingestion required.

## Setup (5 minutes)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your OpenAI API key
cat > config/secrets/config.json << 'EOFINNER'
{
  "OPENAI_API_KEY": "sk-your-key-here",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}
EOFINNER

# 4. Launch!
./run_web_ui.sh
```

Access at: http://localhost:8000

## What's Included

✓ Source code
✓ Vector database (2,168 chunks from 136 PDFs)
✓ Configuration files
✓ Documentation

## What You Need

✓ Python 3.11+
✓ OpenAI API key
✓ Internet (for pip install and API calls)

NO PDF corpus needed - it's already processed!

## Verification

```bash
# Check status
python src/main.py status

# Should show:
# ✓ Vector DB found (2168 chunks, 136 files)
```

See DEPLOYMENT.md for troubleshooting.
EOF

# Create archive
echo ""
echo "📦 Creating archive (this may take a minute)..."
cd "$PACKAGE_DIR"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
cd ..

# Get sizes
TOTAL_SIZE=$(du -sh "portable_package/$PACKAGE_NAME" | cut -f1)
ARCHIVE_SIZE=$(du -sh "portable_package/$PACKAGE_NAME.tar.gz" | cut -f1)

# Show results
echo ""
echo "=========================================="
echo "✅ Complete package created!"
echo "=========================================="
echo ""
echo "📦 Archive: portable_package/$PACKAGE_NAME.tar.gz"
echo "📏 Uncompressed: $TOTAL_SIZE"
echo "📏 Compressed: $ARCHIVE_SIZE"
echo ""
echo "🚀 This package is READY TO USE!"
echo ""
echo "Recipient needs to:"
echo "  1. Extract archive"
echo "  2. Install Python dependencies"
echo "  3. Add OpenAI API key"
echo "  4. Launch web UI"
echo ""
echo "NO PDF corpus or ingestion needed!"
echo ""
echo "=========================================="
echo ""
