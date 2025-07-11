import os
import signal
import time
import threading
from threading import Thread

from logger import setup_logger, setup_library_loggers
from reddit import stream_submissions, stream_comments

# Create a global shutdown event
shutdown_event = threading.Event()

# Logger Initialization
log_level = os.getenv("LOG_LEVEL", "INFO")
app_logger = setup_logger("app", log_level)
setup_library_loggers(log_level)

def main():
    def handle_shutdown(signum, frame):
        app_logger.info(f"Received signal {signum}. Initiating shutdown...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Start threads
    t1 = Thread(target=stream_comments, name="CommentWatcher", daemon=True)
    t2 = Thread(target=stream_submissions, name="SubmissionWatcher", daemon=True)

    t1.start()
    t2.start()

    # Wait for shutdown signal
    while not shutdown_event.is_set():
        time.sleep(1)

    app_logger.info("Shutdown signal received. Waiting for threads to exit...")

    t1.join(timeout=10)
    t2.join(timeout=10)

    app_logger.info("All threads shut down. Exiting.")

if __name__ == '__main__':
    main()
