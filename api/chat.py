from flask import Flask, request, jsonify
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import get_response

app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    history = data.get('history', [])
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = get_response(prompt, history)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel needs this
if __name__ != '__main__':
    # For Vercel serverless
    application = app
