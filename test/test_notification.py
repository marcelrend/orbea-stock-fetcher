from unittest import TestCase
from app_secrets import notification_secret
from stockfetcher.notification import Notification


class NotificationTest(TestCase):
    def test_send(self):
        Notification.send(secret=notification_secret, status="test")
