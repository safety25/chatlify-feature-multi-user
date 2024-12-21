from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import users_collection, messages_collection
from kafka_producer import send_message_to_kafka
from flask_cors import CORS
from flask_socketio import SocketIO , join_room, leave_room # Fix: Import SocketIO
import threading
from datetime import datetime


from kafka_consumer import start_kafka_consumer_for_user



# App initialization
app = Flask(__name__)
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, async_mode="threading")  # Explicit async_mode

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")
    
    if users_collection.find_one({"phone": phone}):
        return jsonify({"error": "Phone number already registered"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"phone": phone, "username": username, "password": hashed_password})
    return jsonify({"message": "User created successfully"}), 201

import threading

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        # Start a Kafka consumer for the user in a new thread
        consumer_thread = threading.Thread(target=start_kafka_consumer_for_user, args=(username,))
        consumer_thread.daemon = True
        consumer_thread.start()

        return jsonify({"message": "Login successful", "username": username}), 200
    return jsonify({"error": "Invalid username or password"}), 401


# get all existing users frome db
@app.route("/get_users", methods=["GET"])
def get_all_users():
    users = users_collection.find({}, {"_id": 0, "username": 1, "phone": 1})
    return jsonify(list(users)), 200

# get chat history between two users
@app.route("/chat/history", methods=["POST"])
def chat_history():
    """
    Retrieve chat history between two users.
    """
    data = request.json
    sender = data.get("sender")  # Username of the sender
    receiver = data.get("receiver")  # Username of the receiver

    if not sender or not receiver:
        return jsonify({"error": "Sender and receiver are required"}), 400

    # Query messages from the MongoDB collection
    messages = messages_collection.find(
        {
            "$or": [
                {"sender": sender, "receiver": receiver},  # Messages sent by the sender to the receiver
                {"sender": receiver, "receiver": sender}   # Messages sent by the receiver to the sender
            ]
        },
        {"_id": 0}  # Exclude MongoDB's _id field
    ).sort("timestamp", 1)  # Sort messages by timestamp (ascending)

    # Convert messages to a list and return as JSON
    return jsonify(list(messages)), 200

@app.route("/chat/send", methods=["POST"])
def send_message():
    data = request.json
    sender = data.get("sender")
    receiver = data.get("receiver")
    content = data.get("content")

    # Generate topic dynamically
    topic = f"chat.{sender}.{receiver}" if sender < receiver else f"chat.{receiver}.{sender}"

    # Produce the message to Kafka
    message = {
        "sender": sender,
        "receiver": receiver,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    send_message_to_kafka(topic, receiver, message)
    # Save the message in MongoDB for persistence
    messages_collection.insert_one(message)
    socketio.emit('new_message', message, room=receiver)

    return jsonify({"message": "Message sent successfully"}), 200

@socketio.on('join')
def handle_join(data):
    username = data.get('username')  # Get username from the client
    join_room(username)  # Add the user to their room
    print(f"User {username} joined their room.")

# Optionally, handle when a user leaves the room
@socketio.on('leave')
def handle_leave(data):
    username = data.get('username')
    leave_room(username)  # Remove the user from the room
    print(f"User {username} left their room.")

@socketio.on('new_message')
def handle_new_message(data):
    receiver = data.get('receiver')  # Username of the recipient
    socketio.emit('message_received', data, room=receiver)  # Send the message to the recipient's room
    print(f"Message sent to {receiver}'s room: {data}")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002, allow_unsafe_werkzeug=True)

