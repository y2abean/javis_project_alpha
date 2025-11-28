from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add current directory to path to import chatbot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import get_response

app = Flask(__name__)
# Enable CORS for local development and production domain
CORS(app, resources={r"/chat": {"origins": ["http://localhost:5173", "https://projectneuron.cfd"]}})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = get_response(prompt)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting NEURON Backend Server on port 5000...")
    app.run(port=5000, debug=True)
