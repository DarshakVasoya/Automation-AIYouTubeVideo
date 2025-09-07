import os
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
import requests
from pymongo import MongoClient


# Load environment variables from .env file (if present)
load_dotenv()


def _get_collection():
	"""Return the MongoDB collection for manhwa documents.

	This is done lazily to avoid connecting at import time.
	Requires env var MONGO_DB to be set (connection string).
	"""
	mongo_uri = os.environ.get("MONGO_DB")
	if not mongo_uri:
		raise ValueError("MONGO_DB environment variable not set")
	client = MongoClient(mongo_uri)
	db = client["admin"]
	return db["manhwa"]


def fetch_one_chapter(manhwa_url: str, chapternum: str):
	"""Fetch images for a single chapter from MongoDB.

	Args:
		manhwa_url: URL key of the manhwa document.
		chapternum: Chapter identifier (e.g., "Chapter 1").

	Returns:
		List[PIL.Image.Image]: loaded RGB page images for the chapter.
	"""
	collection = _get_collection()
	doc = collection.find_one({"url": manhwa_url})
	if not doc:
		raise ValueError(f"No manhwa found with url {manhwa_url}")

	# Find requested chapter
	chapter = next((ch for ch in doc.get("chapters", []) if ch.get("chapternum") == chapternum), None)
	if not chapter:
		raise ValueError(f"Chapter {chapternum} not found for {manhwa_url}")

	images = []
	for img_url in chapter.get("images", []):
		try:
			response = requests.get(img_url, timeout=15)
			response.raise_for_status()
			img = Image.open(BytesIO(response.content)).convert("RGB")
			images.append(img)
		except Exception as e:
			print(f"Failed to fetch {img_url}: {e}")

	print(f"Downloaded {len(images)} images for {chapternum}")
	return images


if __name__ == "__main__":
	# Optional quick test (adjust values as needed)
	url = "https://kingofshojo.com/manga/after-the-school-belle-dumped-me-i-became-a-martial-arts-god/"
	ch = "Chapter 1"
	imgs = fetch_one_chapter(url, ch)
	print(f"Total pages: {len(imgs)}")
