# /// script
# requires-python = ">=3.12"
# [tool.swiftgram]
# id = "document-example"
# name = "Send message text as a document"
# version = "1.0"
# sdk-version = ">=1.1"
# permissions = ["incomingMessages", "menus", "sendMessages", "sendMedia"]
# [[tool.swiftgram.menus]]
# id = "export-text"
# title = "Send text document"
# location = "message"
# action = "showText"
# ///
from uuid import uuid4

from swiftgram import BasePlugin, Event


class Plugin(BasePlugin):
    def on_menu(self, event: Event, menu_id: str) -> str:
        if not event.chat:
            return "No chat selected."
        path = self.data_directory / f"message-{uuid4().hex}.txt"
        path.write_text(event.text, encoding="utf-8")
        self.send_media(event.chat, str(path), kind="document")
        return "Document queued."
