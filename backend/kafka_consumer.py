from kafka import KafkaConsumer
from flask_socketio import SocketIO

import json

from kafka.admin import KafkaAdminClient

def get_user_topics(username):
    admin_client = KafkaAdminClient(bootstrap_servers="localhost:9092")
    all_topics = admin_client.list_topics()
    user_topics = [topic for topic in all_topics if topic.startswith(f"chat.{username}")]
    admin_client.close()
    return user_topics

def start_kafka_consumer_for_user(username):
    consumer = KafkaConsumer(
        bootstrap_servers='localhost:9092',
        group_id=f"{username}_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    # Fetch and subscribe to topics
    topics = get_user_topics(username)
    consumer.subscribe(topics)

    for message in consumer:
        print(f"Received message: {message.value}")
        # Emit the message to the connected client using Socket.IO
        socketio.emit('new_message', message.value, room=username)
