from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)

db = client["codementor"]

reviews = db["reviews"]
users = db["users"]
redo_list = db["redo_list"]
revision_queue = db["revision_queue"]
