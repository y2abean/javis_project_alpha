from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Add current directory to path to import chatbot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import get_response

# Configure Flask to serve React build files
app = Flask(__name__, 
            static_folder='vite-react-app/dist',
            static_url_path='')

# Enable CORS for local development and production domain
CORS(app, resources={r"/chat": {"origins": ["http://localhost:5173", "https://projectneuron.cfd"]}})

# Serve React App
@app.route('/')
def serve_react():
    return send_from_directory(app.static_folder, 'index.html')

# API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    history = data.get('history', [])  # Get history from frontend
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = get_response(prompt, history) # Pass history
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Catch-all route to serve React for client-side routing
@app.route('/<path:path>')
def serve_static(path):
    # Serve static assets (JS, CSS, images)
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # For any other path, serve index.html (React Router handles it)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("Starting NEURON Backend Server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
