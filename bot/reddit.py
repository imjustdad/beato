import os
import praw
import re
import time
from logger import setup_logger
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

# Chord pattern matching
chord_progression_pattern = re.compile(
    r'(\s|^)(I IV V|I V vi IV|ii V I|vi IV I V|I vi IV V|iii vi IV V|I IV vi V|I vi ii V|IV V I|I iii IV V|1 4 5|1 5 6 4|2 5 1|6 4 1 5|1 6 4 5|3 6 4 5|1 4 6 5|1 6 2 5|4 5 1|1 3 4 5)(\?+|!+|\.+|\,+)?(\s|$)'
)
chord_names_pattern = re.compile(
    r'(\s|^)(C|C#|D|D#|E|F|F#|G|G#|A|A#|B|Cb|Db|Eb|Fb|Gb|Ab|Bb)(m|7|m7|dim|aug|sus[24]|6|9|11|13|#9|b5|b9|#5|maj|maj7|maj9|7b5|m7b5)?(\?+|!+|\.+|\,+)?(\s|$)'
)

def is_pattern_matched(text: str):
    return chord_names_pattern.search(text) or chord_progression_pattern.search(text)


def stream_submissions():
    logger.info(f"Started watching new submissions on r/{SUBREDDIT_NAME}...")

    while True:
        try:
            for submission in subreddit.stream.submissions(skip_existing=True):
                match = is_pattern_matched(submission.title)
                if match:
                    logger.info(
                        f"Submission pattern matched - pattern: '{match.group()}' | id: {submission.id} | link: {submission.url}\n{submission.title}"
                    )
                    if not is_submission_persisted(submission.id):
                        logger.info(f"Saving new submission: {submission.title}")
                        save_submission(submission)

        except Exception as e:
            logger.error(f"Error in submission stream: {e}. Retrying in 10 seconds...")
            time.sleep(10)


def stream_comments():
    logger.info(f"Started watching new comments on r/{SUBREDDIT_NAME}...")

    while True:
        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                match = is_pattern_matched(comment.body)
                if match:
                    logger.info(
                        f"Comment pattern matched - pattern: '{match.group()}' | id: {comment.id} | link: {comment.permalink}\n{comment.body}"
                    )
                    if not is_comment_persisted(comment.id):
                        logger.info(f"Saving new comment: {comment.id}")
                        save_comment(comment)

        except Exception as e:
            logger.error(f"Error in comment stream: {e}. Retrying in 10 seconds...")
            time.sleep(10)
