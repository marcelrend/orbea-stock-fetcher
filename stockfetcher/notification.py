import requests
from stockfetcher.secrets_dataclasses import NotificationSecrets


class Notification:
    @staticmethod
    def send(secret: NotificationSecrets):
        url = "https://api.pushbullet.com/v2/pushes"

        # Headers for the request
        headers = {
            "Access-Token": secret.api_secret,
            "Content-Type": "application/json",
        }

        # Data for the push
        data = {
            "type": "note",
            "title": "Stock updater error",
            "body": "To do",
        }

        # Send the request
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
