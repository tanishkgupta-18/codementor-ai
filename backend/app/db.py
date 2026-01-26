from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["codementor"]
reviews = db["reviews"]
users = db["users"]
redo_list = db["redo_list"]
revision_queue = db["revision_queue"]