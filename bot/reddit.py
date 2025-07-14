import os
import praw
import re
import time
from logger import setup_logger
from llm import query_llm
from mongo import is_submission_persisted, save_submission, is_comment_persisted, save_comment

logger = setup_logger("reddit")

# Environment
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
SUBREDDIT_NAME = os.getenv("REDDIT_SUBREDDIT", "patfinnerty")

# Fail fast if missing config
if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
    logger.critical("Missing one or more required Reddit environment variables.")
    raise RuntimeError("Missing Reddit credentials.")

# PRAW Setup
praw_config = {
    "client_id": REDDIT_CLIENT_ID,
    "client_secret": REDDIT_CLIENT_SECRET,
    "user_agent": REDDIT_USER_AGENT,
    "ratelimit_seconds": 600
}

reddit = praw.Reddit(**praw_config)
subreddit = reddit.subreddit(SUBREDDIT_NAME)


def stream_submissions():
    logger.info(f"Started watching new submissions on r/{SUBREDDIT_NAME}...")

    while True:
        try:
            for submission in subreddit.stream.submissions(skip_existing=False):
                llm_response = query_llm(submission.title)
                print("LLM Response: ", llm_response)

                if llm_response and llm_response.get("is_beato_meme") == True:
                    if not is_submission_persisted(submission.id):
                        logger.info(f"Saving new submission: {submission.title}")
                        save_submission(submission)

                elif llm_response and llm_response.get("is_beato_meme") == False:
                    logger.debug(f"Submission processed, no patterns matched for title: {submission.title}")

        except Exception as e:
            logger.error(f"Error in submission stream: {e}. Retrying in 10 seconds...")
            time.sleep(10)


def stream_comments():
    logger.info(f"Started watching new comments on r/{SUBREDDIT_NAME}...")

    while True:
        try:
            for comment in subreddit.stream.comments(skip_existing=False):
                llm_response = query_llm(comment.body)
                print("LLM Response: ", llm_response)

                if llm_response and llm_response.get("is_beato_meme") == True:
                    if not is_comment_persisted(comment.id):
                        logger.info(f"Saving new comment: {comment.id}")
                        save_comment(comment)

                elif llm_response and llm_response.get("is_beato_meme") == False:
                    logger.debug(f"Comment processed, no patterns matched for body: {comment.body}")

        except Exception as e:
            logger.error(f"Error in comment stream: {e}. Retrying in 10 seconds...")
            time.sleep(10)
