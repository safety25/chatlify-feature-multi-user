from confluent_kafka.admin import AdminClient, NewTopic
from kafka import KafkaProducer
import json
import time



# Kafka configuration
KAFKA_BROKER = "kafka:9092"  # Docker service name for Kafka
RETRY_INTERVAL = 5  # Seconds to wait between retries
MAX_RETRIES = 12  # Maximum number of retries (total 1 minute if RETRY_INTERVAL is 5)

def wait_for_kafka():
    """
    Wait for Kafka broker to become available and create required topics.
    """
    admin_client = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    retries = 0

    while retries < MAX_RETRIES:
        try:
            # Attempt to get metadata to verify the broker is reachable
            admin_client.list_topics(timeout=5)
            print("Kafka broker is available.")
            break
        except Exception as e:
            print(f"Kafka broker not available yet ({e}). Retrying in {RETRY_INTERVAL} seconds...")
            retries += 1
            time.sleep(RETRY_INTERVAL)
    else:
        raise Exception("Failed to connect to Kafka broker after retries.")


# Wait for Kafka broker to be ready and create topics
wait_for_kafka()

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

def send_message_to_kafka(topic, key, message):
    """
    Send a message to Kafka.
    :param topic: The Kafka topic.
    :param key: The key for partitioning.
    :param message: The message to send.
    """
    producer.send(topic, key=key, value=message)
    producer.flush()  # Ensure the message is sent immediately
    print(f"Message sent to topic {topic}: {message}")
