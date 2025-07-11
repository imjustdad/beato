import os
from threading import Thread
from logger import setup_logger, setup_library_loggers
from reddit import stream_submissions, stream_comments

# Logger Initialization
log_level = os.getenv("LOG_LEVEL", "INFO")
app_logger = setup_logger("app", log_level)
setup_library_loggers(log_level)

def main():
    t1 = Thread(target=stream_comments, name="CommentWatcher", daemon=True)
    t2 = Thread(target=stream_submissions, name="SubmissionWatcher", daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == '__main__':
    main()
