# /// script
# requires-python = ">=3.12"
# [tool.swiftgram]
# id = "reply-example"
# name = "Reply command example"
# version = "1.0"
# sdk-version = ">=1.1"
# description = "Replies to incoming !ping messages with pong."
# permissions = ["incomingMessages", "readMessages", "sendMessages"]
# hooks = [{ event = "message", name = "message" }]
# ///
from swiftgram import BasePlugin, Event


class Plugin(BasePlugin):
    def on_message(self, event: Event) -> None:
        if event.text == "!ping" and event.chat and isinstance(event.message, dict):
            self.send_message(event.chat, "pong", reply_to=event.message["id"])
