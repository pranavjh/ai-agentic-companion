"""
Web UI for AI Agentic Companion

Flask application providing web interface for:
- Q&A Chatbot
- LinkedIn Post Generator
- Blog Generator
- Podcast Generator
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from pathlib import Path
import sys
import os
import traceback
from datetime import datetime
import secrets

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.qa_agent import QAAgent
from generators.linkedin_generator import LinkedInGenerator
from generators.blog_generator import BlogGenerator
from generators.podcast_generator import PodcastGenerator

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize generators (reuse instances)
qa_agents = {}  # Store per-session QA agents
linkedin_gen = LinkedInGenerator()
blog_gen = BlogGenerator()
podcast_gen = PodcastGenerator()


def get_qa_agent():
    """Get or create QA agent for current session"""
    session_id = session.get('session_id')
    if not session_id:
        session_id = secrets.token_hex(8)
        session['session_id'] = session_id

    if session_id not in qa_agents:
        qa_agents[session_id] = QAAgent()

    return qa_agents[session_id]


@app.route('/')
def index():
    """Main page with tabs"""
    return render_template('index.html')


# ============================================================
# Q&A Chatbot API
# ============================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle Q&A chat messages"""
    try:
        data = request.json
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'error': 'Question is required'}), 400

        # Handle special commands
        if question.lower() == 'clear':
            agent = get_qa_agent()
            agent.clear_history()
            return jsonify({
                'type': 'system',
                'message': 'Conversation history cleared'
            })

        # Get answer from QA agent
        agent = get_qa_agent()
        result = agent.answer(question, verbose=True)

        return jsonify({
            'type': 'answer',
            'answer': result['answer'],
            'sources': result['sources'],
            'num_chunks': result['num_chunks'],
            'conversation_length': result['conversation_length']
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ============================================================
# LinkedIn Generator API
# ============================================================

@app.route('/api/generate/linkedin', methods=['POST'])
def generate_linkedin():
    """Generate LinkedIn post"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        format_type = data.get('format', 'text')
        length = data.get('length', 'medium')
        num_hashtags = data.get('num_hashtags', 5)
        custom_hashtags = data.get('custom_hashtags', '')
        create_images = data.get('create_images', False)

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Parse custom hashtags
        custom_tags = None
        if custom_hashtags:
            custom_tags = [tag.strip() if tag.startswith('#') else f'#{tag.strip()}'
                          for tag in custom_hashtags.split(',')]

        # Generate post
        result = linkedin_gen.generate(
            topic=topic,
            format_type=format_type,
            length=length,
            num_hashtags=num_hashtags,
            custom_hashtags=custom_tags,
            create_images=create_images
        )

        # Format output
        output = linkedin_gen.format_output(result)

        # Prepare download info
        download_files = []
        if result.get('image_paths'):
            download_files = [
                {'name': Path(p).name, 'path': p}
                for p in result['image_paths']
            ]

        return jsonify({
            'success': True,
            'content': output,
            'format': format_type,
            'word_count': result.get('word_count'),
            'sources': result.get('sources', []),
            'download_files': download_files
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ============================================================
# Blog Generator API
# ============================================================

@app.route('/api/generate/blog', methods=['POST'])
def generate_blog():
    """Generate blog article"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        length = data.get('length', 'medium')
        create_banner = data.get('create_banner', True)

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Generate blog
        result = blog_gen.generate(
            topic=topic,
            length=length,
            create_banner=create_banner
        )

        # Read the generated markdown file
        # The result contains the file path in the blog_gen.output_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = blog_gen._sanitize_filename(topic)
        blog_path = blog_gen.output_dir / f"{timestamp}_{safe_topic}.md"

        # Get the actual saved file path from recent files
        blog_files = sorted(blog_gen.output_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        if blog_files:
            blog_path = blog_files[0]

        with open(blog_path, 'r') as f:
            content = f.read()

        # Prepare download info
        download_files = [
            {'name': blog_path.name, 'path': str(blog_path), 'type': 'markdown'}
        ]

        if result.get('banner_path'):
            download_files.append({
                'name': Path(result['banner_path']).name,
                'path': result['banner_path'],
                'type': 'image'
            })

        return jsonify({
            'success': True,
            'title': result['title'],
            'content': content,
            'word_count': result['word_count'],
            'sources': result.get('sources', []),
            'banner_path': result.get('banner_path'),
            'download_files': download_files
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ============================================================
# Podcast Generator API
# ============================================================

@app.route('/api/generate/podcast', methods=['POST'])
def generate_podcast():
    """Generate podcast episode"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        length = data.get('length', 10)
        format_type = data.get('format', 'conversation')
        host_voice = data.get('host_voice', 'onyx')
        guest_voice = data.get('guest_voice', 'nova')
        generate_audio = data.get('generate_audio', True)

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Generate podcast
        result = podcast_gen.generate(
            topic=topic,
            length=int(length),
            format_type=format_type,
            host_voice=host_voice,
            guest_voice=guest_voice,
            generate_audio=generate_audio
        )

        # Get the generated transcript file
        podcast_files = sorted(podcast_gen.output_dir.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)
        transcript_path = podcast_files[0] if podcast_files else None

        with open(transcript_path, 'r') as f:
            transcript = f.read()

        # Prepare download info
        download_files = [
            {'name': transcript_path.name, 'path': str(transcript_path), 'type': 'transcript'}
        ]

        if result.get('audio_path'):
            download_files.append({
                'name': Path(result['audio_path']).name,
                'path': result['audio_path'],
                'type': 'audio'
            })

        return jsonify({
            'success': True,
            'transcript': transcript,
            'format': format_type,
            'word_count': result['word_count'],
            'sources': result.get('sources', []),
            'audio_path': result.get('audio_path'),
            'download_files': download_files
        })

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ============================================================
# File Download API
# ============================================================

@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    """Download generated files"""
    try:
        # Security: only allow downloads from output directory
        base_path = Path(__file__).parent.parent.parent / 'output'
        file_path = base_path / filepath

        # Verify file exists and is within output directory
        if not file_path.exists() or not file_path.is_relative_to(base_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# Status and Info API
# ============================================================

@app.route('/api/status')
def status():
    """Get system status"""
    try:
        import yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Get vector DB stats
        from knowledge.vector_store import VectorStoreManager
        vector_db_path = Path(config['vector_db']['persist_directory'])

        stats = {'chunks': 0, 'files': 0}
        if vector_db_path.exists():
            vs = VectorStoreManager(
                persist_directory=str(vector_db_path),
                collection_name=config['vector_db']['collection_name']
            )
            db_stats = vs.get_stats()
            stats = {
                'chunks': db_stats['total_chunks'],
                'files': db_stats['processed_files']
            }

        return jsonify({
            'status': 'ready',
            'model': config['models']['llm'],
            'knowledge_base': stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voices')
def get_voices():
    """Get available TTS voices"""
    return jsonify({
        'voices': [
            {'value': 'alloy', 'label': 'Alloy - Neutral, balanced'},
            {'value': 'echo', 'label': 'Echo - Male, clear and articulate'},
            {'value': 'fable', 'label': 'Fable - Male, warm and friendly'},
            {'value': 'onyx', 'label': 'Onyx - Male, deep and authoritative'},
            {'value': 'nova', 'label': 'Nova - Female, warm and engaging'},
            {'value': 'shimmer', 'label': 'Shimmer - Female, bright and energetic'}
        ]
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AI Agentic Companion Web UI")
    print("="*60)
    print("\nStarting web server...")
    print("\n📍 Access the application at: http://localhost:5000")
    print("\n✨ Features available:")
    print("   • Q&A Chatbot")
    print("   • LinkedIn Post Generator")
    print("   • Blog Article Generator")
    print("   • Podcast Episode Generator")
    print("\n⏹  Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
