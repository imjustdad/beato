import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from logger import setup_logger
from discord import send_discord_webhook

logger = setup_logger("mongo")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Define it in your Docker Compose environment.")

client = MongoClient(
    MONGO_URI,
    server_api=MongoClient.SERVER_API_VERSION_1
)
database = client["main"]
submissions_collection = database["submissions"]
comments_collection = database["comments"]


def convert_to_datetime(utc_time):
    """Converts a UTC timestamp to a timezone-aware datetime object in UTC."""
    return datetime.fromtimestamp(utc_time, tz=timezone.utc)


def is_submission_persisted(submission_id: str) -> bool:
    exists = submissions_collection.find_one({"_id": submission_id}) is not None
    logger.debug(f"Submission exists: {exists} (ID: {submission_id})")
    return exists


def save_submission(submission) -> None:
    """Save a Reddit submission to MongoDB and trigger a Discord webhook."""
    data = {
        "_id": submission.id,
        "title": submission.title,
        "author": {
            "id": submission.author.id,
            "name": submission.author.name,
            "url": f"https://www.reddit.com/u/{submission.author.name}",
        },
        "url": submission.url,
        "created": convert_to_datetime(submission.created_utc),
    }

    try:
        submissions_collection.insert_one(data)
        send_discord_webhook("submission", data)
        logger.info(f"Submission {submission.id} saved to database.")
    except PyMongoError as e:
        logger.warning(f"Retrying insert for submission {submission.id} after error: {e}")
        try:
            submissions_collection.insert_one(data)
            send_discord_webhook("submission", data)
            logger.info(f"Submission {submission.id} saved on retry.")
        except PyMongoError as e:
            logger.error(f"Failed to save submission {submission.id}: {e}")


def is_comment_persisted(comment_id: str) -> bool:
    exists = comments_collection.find_one({"_id": comment_id}) is not None
    logger.debug(f"Comment exists: {exists} (ID: {comment_id})")
    return exists


def save_comment(comment) -> None:
    """Save a Reddit comment to MongoDB and trigger a Discord webhook."""
    data = {
        "_id": comment.id,
        "body": comment.body,
        "author": {
            "id": comment.author.id,
            "name": comment.author.name,
            "url": f"https://www.reddit.com/u/{comment.author.name}",
        },
        "submission": {
            "id": comment.submission.id,
            "title": comment.submission.title,
            "author": {
                "id": comment.submission.author.id,
                "name": comment.submission.author.name,
                "url": f"https://www.reddit.com/u/{comment.submission.author.name}",
            },
            "url": comment.submission.url,
            "created": convert_to_datetime(comment.submission.created_utc),
        },
        "permalink": f"https://www.reddit.com{comment.permalink}",
        "created": convert_to_datetime(comment.created_utc),
    }

    try:
        comments_collection.insert_one(data)
        send_discord_webhook("comment", data)
        logger.info(f"Comment {comment.id} saved to database.")
    except PyMongoError as e:
        logger.warning(f"Retrying insert for comment {comment.id} after error: {e}")
        try:
            comments_collection.insert_one(data)
            send_discord_webhook("comment", data)
            logger.info(f"Comment {comment.id} saved on retry.")
        except PyMongoError as e:
            logger.error(f"Failed to save comment {comment.id}: {e}")
