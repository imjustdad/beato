from threading import Thread
from logger import setup_logger, setup_library_loggers
import os
import re
import praw
from discord import send_discord_webhook
from mongo import is_submission_persisted, save_submission, is_comment_persisted, save_comment

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

chord_progression_pattern = re.compile(
    r'(\s|^)(I IV V|I V vi IV|ii V I|vi IV I V|I vi IV V|iii vi IV V|I IV vi V|I vi ii V|IV V I|I iii IV V|1 4 5|1 5 6 4|2 5 1|6 4 1 5|1 6 4 5|3 6 4 5|1 4 6 5|1 6 2 5|4 5 1|1 3 4 5)(\?+|!+|\.+|\,+)?(\s|$)')
chord_names_pattern = re.compile(
    r'(\s|^)(C|C#|D|D#|E|F|F#|G|G#|A|A#|B|Cb|Db|Eb|Fb|Gb|Ab|Bb)(m|7|m7|dim|aug|sus[24]|6|9|11|13|#9|b5|b9|#5|maj|maj7|maj9|7b5|m7b5)?(\?+|!+|\.+|\,+)?(\s|$)')


def is_pattern_matched(text):
    return chord_names_pattern.search(text) or chord_progression_pattern.search(text)

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

                save_submission(submission)


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

                save_comment(comment)


def main():
    t1 = Thread(target=stream_comments, name="CommentWatcher", daemon=True)
    t2 = Thread(target=stream_submissions, name="SubmissionWatcher", daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == '__main__':
    main()
