# Deployment Guide - AI Agentic Companion v1.0.0

This guide explains how to deploy the AI Agentic Companion on a new computer.

## 📋 Prerequisites

- **Python:** 3.11 or higher
- **OpenAI API Key:** Get from https://platform.openai.com/api-keys
- **PDF Corpus:** Your AI and Agentic PDF files (optional if using git method)
- **Disk Space:** ~1GB for dependencies + corpus size

## 🚀 Deployment Options

### Option 1: Git Clone (Recommended)

**Best for:** Most users, easiest updates

```bash
# 1. Clone repository
git clone https://github.com/pranavjh/ai-agentic-companion.git
cd ai-agentic-companion

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
mkdir -p config/secrets
cat > config/secrets/config.json << 'EOF'
{
  "OPENAI_API_KEY": "sk-your-key-here",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}
EOF

# 5. Update corpus path in config/config.yaml
# Edit the 'corpus.path' to point to your PDFs

# 6. Ingest knowledge base
python src/main.py ingest

# 7. Launch web UI
./run_web_ui.sh
```

Access at: **http://localhost:8000**

---

### Option 2: Portable Package

**Best for:** Offline deployment, no git available

#### Creating the Package (on source machine)

```bash
# Run the packaging script
./create_portable_package.sh
```

This creates `portable_package/ai-agentic-companion-v1.0.0.tar.gz` (~100KB)

#### Deploying the Package (on new machine)

```bash
# 1. Extract package
tar -xzf ai-agentic-companion-v1.0.0.tar.gz
cd ai-agentic-companion-v1.0.0

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cat > config/secrets/config.json << 'EOF'
{
  "OPENAI_API_KEY": "sk-your-key-here",
  "OPENAI_API_BASE": "https://api.openai.com/v1/"
}
EOF

# 5. Update corpus path in config/config.yaml
# Point to your PDF files location

# 6. Ingest knowledge base
python src/main.py ingest

# 7. Launch
./run_web_ui.sh
```

---

## 📦 What Gets Included/Excluded

### ✅ Included in Package
- Source code (`src/`)
- Configuration templates (`config/`)
- Requirements (`requirements.txt`)
- Documentation (`README.md`, etc.)
- Launch scripts (`run_web_ui.sh`)

### ❌ Excluded from Package
- Virtual environment (`venv/`) - recreate on new machine
- Vector database (`data/vector_db/`) - regenerate via ingestion
- Generated outputs (`output/`) - created as you use the app
- API keys (`config/secrets/`) - security
- Git history (`.git/`) - if using package method

---

## 🔄 Transferring Vector Database (Optional)

If you want to avoid re-ingesting (saves time but increases package size):

### On Source Machine
```bash
# Create package with vector DB
tar -czf ai-companion-with-db.tar.gz \
    --exclude='venv' \
    --exclude='output' \
    --exclude='config/secrets' \
    --exclude='.git' \
    --exclude='__pycache__' \
    .
```

### On New Machine
```bash
# Extract
tar -xzf ai-companion-with-db.tar.gz

# Setup (skip ingestion step)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add API keys
# ... (as above)

# Launch directly
./run_web_ui.sh
```

**Note:** Vector DB can be large (100MB-1GB depending on corpus)

---

## 🛠️ Post-Deployment Setup

### Configure Corpus Path

Edit `config/config.yaml`:

```yaml
corpus:
  path: "/path/to/your/PDFs"  # Update this
  file_types: ["pdf"]
  max_file_size_mb: 50
```

### Run Ingestion

```bash
# Process all PDFs
python src/main.py ingest

# Force reprocessing
python src/main.py ingest --force

# Check status
python src/main.py status
```

**Time Required:** 10-30 minutes for ~150 PDFs (944MB)

---

## ✅ Verification

### Test CLI
```bash
# Activate venv first
source venv/bin/activate

# Test Q&A
python src/main.py chat "What is RAG?"

# Test LinkedIn generator
python src/main.py generate linkedin "AI trends"

# Test blog generator
python src/main.py generate blog "Multi-agent systems"

# Test podcast generator
python src/main.py generate podcast "Future of AI" --no-audio
```

### Test Web UI
```bash
./run_web_ui.sh
# Open http://localhost:8000 in browser
# Try each tab
```

---

## 🔧 Troubleshooting

### "No module named 'xxx'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "FileNotFoundError: config/config.yaml"
Make sure you're in the project root directory:
```bash
pwd  # Should show .../ai-agentic-companion
ls config/config.yaml  # Should exist
```

### "No such file or directory: config/secrets/config.json"
Create the secrets file:
```bash
mkdir -p config/secrets
nano config/secrets/config.json
# Add your API key
```

### Port 8000 already in use
Edit `src/web/app.py` line 377:
```python
app.run(debug=True, host='0.0.0.0', port=9000)  # Change port
```

### ChromaDB errors
Delete and recreate:
```bash
rm -rf data/vector_db
python src/main.py ingest
```

### Out of memory during ingestion
Reduce batch size:
```bash
python src/main.py ingest --batch-size 5
```

---

## 📝 Platform-Specific Notes

### macOS
- Port 5000 is used by AirPlay (app uses 8000)
- May need to allow Terminal in Privacy settings

### Windows
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- Use `python` instead of `python3`
- May need to run PowerShell as Administrator

### Linux
- Ensure Python 3.11+ is installed
- May need `python3-venv` package: `sudo apt install python3.11-venv`

---

## 🔐 Security Notes

1. **Never commit API keys** to git
2. **Keep `config/secrets/` private**
3. **Use environment variables** for production:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
4. **Firewall:** Web UI binds to `0.0.0.0` - restrict if needed

---

## 📊 Resource Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.11+ |
| RAM | 4GB minimum, 8GB recommended |
| Disk Space | ~1GB + corpus size |
| CPU | Modern multi-core (for parallel processing) |
| Network | Internet for OpenAI API calls |

---

## 🆘 Getting Help

- **Documentation:** README.md
- **Issues:** https://github.com/pranavjh/ai-agentic-companion/issues
- **API Docs:** https://platform.openai.com/docs

---

## ✨ Next Steps After Deployment

1. **Test all features** via Web UI
2. **Customize config** in `config/config.yaml`
3. **Add your PDFs** to corpus
4. **Explore CLI commands** with `--help`
5. **Check version:** `python src/main.py version`

Enjoy your AI Agentic Companion! 🚀
