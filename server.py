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

# Enable CORS - allow all origins for now, will be restricted later
CORS(app, resources={
    r"/chat": {
        "origins": "*",  # Allow all origins initially
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Serve React App
@app.route('/')
def serve_react():
    return send_from_directory(app.static_folder, 'index.html')

# API endpoint
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.json
    prompt = data.get('prompt')
    history = data.get('history', [])  # Get history from frontend
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = get_response(prompt, history) # Pass history
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")  # Log for debugging
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
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting NEURON Backend Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
