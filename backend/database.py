from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://mongo:27017/")
db = client['chat_app']

# Collections for users and messages
users_collection = db['users']
messages_collection = db['messages']
messages_collection.create_index([("sender", 1), ("receiver", 1), ("timestamp", 1)])