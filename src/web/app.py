#!/usr/bin/env python
"""
Atlas AI - Enterprise Web Interface
Professional Flask-based web application with advanced RAG capabilities.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import sys
import json
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.cache_manager import LRUCache
from src.nlp.intent_classifier_v2 import classify_intent_enhanced
from src.responses.knowledge_base import get_response, get_fallback_response
from src.dialogue.manager_v2 import process_message, reset_session

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Global cache for sessions
session_cache = LRUCache(max_size=10000, default_ttl=3600)


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    data = request.get_json()
    message = data.get('message', '').strip()
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    # Process message
    response_data = process_message(session_id, message)
    
    elapsed = (time.time() - start_time) * 1000
    
    return jsonify({
        'response': response_data.get('response', ''),
        'session_id': session_id,
        'processing_time_ms': round(elapsed, 2),
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Atlas AI',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    return jsonify({
        'total_sessions': len(session_cache._cache),
        'uptime': 'N/A',
        'version': '2.0.0',
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)