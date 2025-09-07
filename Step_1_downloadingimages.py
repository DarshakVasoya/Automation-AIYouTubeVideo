
import os
from pymongo import MongoClient
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variable
mongo_uri = os.environ.get("MONGO_DB")
if not mongo_uri:
    raise ValueError("MONGO_DB environment variable not set")
client = MongoClient(mongo_uri)
db = client["admin"]
collection = db["manhwa"]


def fetch_one_chapter(manhwa_url, chapternum):
    """Fetch images for a single chapter from MongoDB."""
    doc = collection.find_one({"url": manhwa_url})
    if not doc:
        raise ValueError(f"No manhwa found with url {manhwa_url}")

    # find requested chapter
    chapter = next((ch for ch in doc["chapters"] if ch["chapternum"] == chapternum), None)
    if not chapter:
        raise ValueError(f"Chapter {chapternum} not found for {manhwa_url}")

    images = []
    for img_url in chapter["images"]:
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            images.append(img)
        except Exception as e:
            print(f"⚠️ Failed to fetch {img_url}: {e}")

    print(f"✅ Downloaded {len(images)} images for {chapternum}")
    return images

# Example usage
chapter_images = fetch_one_chapter(
    "https://kingofshojo.com/manga/after-the-school-belle-dumped-me-i-became-a-martial-arts-god/",
    "Chapter 1"
)

print(f"Total pages: {len(chapter_images)}")
