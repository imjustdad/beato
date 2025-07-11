from threading import Thread
from logger import setup_logger, setup_library_loggers
import os
import re
import logging
import datetime
import json
import requests
import praw
import pymongo
from rich.pretty import pprint
from discord import send_discord_webhook

# set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO")

# initialize app logger
app_logger = setup_logger("app", log_level)

# set up library loggers: praw, prawcore, and pymongo
setup_library_loggers(log_level)


# region Environment Variables
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

MONGO_URI = os.getenv('MONGO_URI')

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# endregion



# region PRAW Configuration
praw_config = {
    'client_id': REDDIT_CLIENT_ID,
    'client_secret': REDDIT_CLIENT_SECRET,
    'user_agent': REDDIT_USER_AGENT,
    'ratelimit_seconds': 600
}

praw_subreddit = 'patfinnerty'
# endregion

# region MongoDB Configuration
client = pymongo.MongoClient(MONGO_URI, server_api=pymongo.server_api.ServerApi(
    version='1', strict=True, deprecation_errors=True))
database = client['main']
submissions_collection = database['submissions']
comments_collection = database['comments']
# endregion

chord_progression_pattern = re.compile(
    r'(\s|^)(I IV V|I V vi IV|ii V I|vi IV I V|I vi IV V|iii vi IV V|I IV vi V|I vi ii V|IV V I|I iii IV V|1 4 5|1 5 6 4|2 5 1|6 4 1 5|1 6 4 5|3 6 4 5|1 4 6 5|1 6 2 5|4 5 1|1 3 4 5)(\?+|!+|\.+|\,+)?(\s|$)')
chord_names_pattern = re.compile(
    r'(\s|^)(C|C#|D|D#|E|F|F#|G|G#|A|A#|B|Cb|Db|Eb|Fb|Gb|Ab|Bb)(m|7|m7|dim|aug|sus[24]|6|9|11|13|#9|b5|b9|#5|maj|maj7|maj9|7b5|m7b5)?(\?+|!+|\.+|\,+)?(\s|$)')


def is_pattern_matched(text):
    return chord_names_pattern.search(text) or chord_progression_pattern.search(text)


def convert_to_datetime(utc_time):
    return datetime.datetime.fromtimestamp(utc_time).strftime('%Y-%m-%d %H:%M:%S')


def is_submission_persisted(submission_id):
    document = submissions_collection.find_one({'_id': submission_id})

    if document:
        app_logger.info(
            f"found submission collection document {document['_id']}")
        app_logger.info(pprint(document))
        return True
    else:
        app_logger.info(f'no submission collection document found')
        return False


def save_submission_to_db(submission):
    data = {
        '_id': submission.id,
        'title': submission.title,
        'author': {
            'id': submission.author.id,
            'name': submission.author.name,
            'url': f'https://www.reddit.com/u/{submission.author.name}'
        },
        'url': submission.url,
        'created': convert_to_datetime(submission.created_utc)
    }

    try:
        document = submissions_collection.insert_one(data)
        inserted_id = document.inserted_id
        inserted_document = submissions_collection.find_one(
            {'_id': inserted_id})

        send_discord_webhook('submission', inserted_document)

        app_logger.info(f'Submission {submission.id} saved to database')
        app_logger.info(f'{pprint(inserted_document)}')

    except Exception as e:
        app_logger.error(f'Error saving submission: {e}')


def is_comment_persisted(comment_id):
    document = comments_collection.find_one({'_id': comment_id})

    if document:
        app_logger.info(
            f"found comment collection document: {document['_id']}")
        app_logger.info(pprint(document))
        return True
    else:
        app_logger.info(f'no comment collection document found')
        return False


def save_comment_to_db(comment):
    data = {
        '_id': comment.id,
        'body': comment.body,
        'author': {
            'id': comment.author.id,
            'name': comment.author.name,
            'url': f'https://www.reddit.com/u/{comment.author.name}'
        },
        'submission': {
            'id': comment.submission.id,
            'title': comment.submission.title,
            'author': {
                'id': comment.submission.author.id,
                'name': comment.submission.author.name,
                'url': f'https://www.reddit.com/u/{comment.submission.author.name}'
            },
            'url': comment.submission.url,
            'created': convert_to_datetime(comment.submission.created_utc)
        },
        'permalink': f'https://www.reddit.com{comment.permalink}',
        'created': convert_to_datetime(comment.created_utc)
    }

    try:
        document = comments_collection.insert_one(data)
        inserted_id = document.inserted_id
        inserted_document = comments_collection.find_one({'_id': inserted_id})

        send_discord_webhook('comment', inserted_document)

        app_logger.info(f'Comment {comment.id} saved to database')
        app_logger.info(f'{pprint(inserted_document)}')

    except Exception as e:
        app_logger.error(f'Error saving comment: {e}')


def stream_submissions():
    app_logger.info(
        f'started watching for new submissions on r/{praw_subreddit}...')

    reddit = praw.Reddit(**praw_config)

    subreddit = reddit.subreddit(praw_subreddit)

    for submission in subreddit.stream.submissions(skip_existing=True):

        match = is_pattern_matched(submission.title)

        if match:
            app_logger.info(
                f'submission pattern matched - pattern: "{match.group()}" id: {submission.id} link: {submission.url}\n{submission.title}')

            if not is_submission_persisted(submission.id):
                app_logger.info(
                    f'saving submission to database: {submission.title}')

                # submission.reply('Beato')

                save_submission_to_db(submission)


def stream_comments():
    app_logger.info(
        f'started watching for new comments on r/{praw_subreddit}...')
    reddit = praw.Reddit(**praw_config)

    subreddit = reddit.subreddit(praw_subreddit)

    for comment in subreddit.stream.comments(skip_existing=True):

        match = is_pattern_matched(comment.body)

        if match:
            app_logger.info(
                f'comment pattern matched - pattern: "{match.group()}" id: {comment.id} link: {comment.permalink}\n{comment.body}')

            if not is_comment_persisted(comment.id):
                app_logger.info(f'saving comment to database: {comment.id}')

                # comment.reply('Beato')

                save_comment_to_db(comment)


def main():
    t1 = Thread(target=stream_comments, name="CommentWatcher", daemon=True)
    t2 = Thread(target=stream_submissions, name="SubmissionWatcher", daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == '__main__':
    main()
