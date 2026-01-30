
from ..steps.api import ApiStep

class Slack:
    @staticmethod
    def post_message(channel: str, message: str, output: str = None):
        """Post a message to Slack."""
        # Uses standard webhook or chat.postMessage?
        # Assuming chat.postMessage for nicer integration, requires token.
        return ApiStep(
            name=output or "slack_notify",
            method="POST",
            url="https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": "Bearer {secrets:slack_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": channel,
                "text": message
            }
        )
