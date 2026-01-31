import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from rich.pretty import pprint

"""
Utilities for interacting with Slack for experiment notification via Wandb Logger.
"""
class SlackUtils:
    _instance = None

    def __new__(cls, token=None):
        """
        Singleton __new__ method.
        Ensures only one instance of SlackUtils exists.
        """
        if cls._instance is None:
            if token is None:
                raise ValueError(
                    "A Slack Token is required for the first initialization."
                )

            # Create the instance
            cls._instance = super(SlackUtils, cls).__new__(cls)

            # Initialize the WebClient only once
            cls._instance.client = WebClient(token=token)
            cls._instance.token = token

        return cls._instance

    def clear_channel(self, channel_id, sleep_interval=1.0):
        """
        Fetches and deletes all messages in a specified channel.
        """
        cursor = None
        deleted_count = 0

        pprint(f"--- Starting cleanup for Channel ID: {channel_id} ---")

        while True:
            try:
                # Fetch history in batches of 100
                response = self.client.conversations_history(  # ty:ignore[unresolved-attribute]
                    channel=channel_id, cursor=cursor, limit=100
                )

                messages = response.get("messages", [])

                if not messages:
                    pprint("No more messages found to delete.")
                    break

                for msg in messages:
                    ts = msg.get("ts")

                    try:
                        # Attempt delete
                        self.client.chat_delete(  # ty:ignore[unresolved-attribute]
                            channel=channel_id, ts=ts
                        )
                        pprint(f"Deleted: {ts}")
                        deleted_count += 1

                        # Rate limit protection (Tier 3 limit)
                        time.sleep(sleep_interval)

                    except SlackApiError as e:
                        error_code = e.response["error"]
                        if error_code == "cant_delete_message":
                            pprint(f"Skipped (Permission denied): {ts}")
                        elif error_code == "message_not_found":
                            pprint(f"Skipped (Already deleted): {ts}")
                        else:
                            pprint(f"Error deleting {ts}: {error_code}")
                # Check for pagination
                if response["has_more"]:
                    cursor = response["response_metadata"]["next_cursor"]
                else:
                    break

            except SlackApiError as e:
                print(f"Critical API Error fetching history: {e.response['error']}")
                break

        print(f"--- Completed. Total messages deleted: {deleted_count} ---")
