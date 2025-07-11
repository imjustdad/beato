import os
import json
import requests
from logger import setup_logger

logger = setup_logger("discord")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_webhook(entity: str, document: dict):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Skipping webhook.")
        return

    if entity == 'comment':
        data = {
            'content': 'A new comment was inserted into MongoDB.',
            'embeds': [
                {
                    'title': 'New Comment',
                    'fields': [
                        {'name': '_id', 'value': str(document['_id']), 'inline': False},
                        {'name': 'body', 'value': document.get('body', ''), 'inline': False},
                        {'name': 'permalink', 'value': document.get('permalink', ''), 'inline': False},
                    ],
                    'color': 3066993
                }
            ]
        }
    elif entity == 'submission':
        data = {
            'content': 'A new submission was inserted into MongoDB.',
            'embeds': [
                {
                    'title': 'New Submission',
                    'fields': [
                        {'name': '_id', 'value': str(document['_id']), 'inline': False},
                        {'name': 'title', 'value': document.get('title', ''), 'inline': False},
                    ],
                    'color': 3066993
                }
            ]
        }
    else:
        logger.warning(f"Unknown entity type '{entity}'")
        return

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 204:
            logger.info(f"{entity} document sent to Discord successfully.")
        else:
            logger.error(f"Failed to send Discord webhook. Status: {response.status_code}, Body: {response.text}")

    except Exception as e:
        logger.error(f"Error sending Discord webhook: {e}")
