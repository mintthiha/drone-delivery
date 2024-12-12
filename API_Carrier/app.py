from flask import Flask, render_template, jsonify, request
from jwt_module import validate_jwt
app = Flask(__name__)

messages = {}

@app.route('/')
def home():
    return jsonify({"carrier": "connected"}), 200

@app.route('/api/shipment/<UPC_ID>', methods=['GET', 'POST'])
def api_messages(UPC_ID):
    if request.method == 'POST':
        # Get the message from the JSON payload
        message_data = request.json.get('message')
        token = request.json.get('token')

        if validate_jwt(token):
          print('valid JWT Token!')
          if message_data:
            messages[UPC_ID] = message_data  # Store the message with UPC_ID as key
            return jsonify({"message": "Message added successfully!"}), 201
          else:
              return jsonify({"error": "No message provided!"}), 400
        else:
            return jsonify({"error": "The JWT Token is either expired or invalid!"}), 500

    if request.method == 'GET':
        # Handle GET request: return message for the specific UPC_ID if exists
      token = request.headers.get("Authorization")

      if not token:
          return jsonify({"error": "Missing authorization token"}), 401

      # Validate the token
      if not validate_jwt(token):
          return jsonify({"error": "Invalid or expired token"}), 403

      if UPC_ID in messages:
          return jsonify({UPC_ID: messages[UPC_ID]}), 200
      else:
          return jsonify({"error": "UPC_ID not found!"}), 404
    # Handle GET request: return all messages
    return jsonify({"messages": list(messages.values())}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)
