# /// script
# requires-python = ">=3.12"
# dependencies = []
# [tool.swiftgram]
# id = "uppercase"
# name = "Uppercase composed messages"
# version = "1.0"
# author = "Swiftgram"
# description = "Converts outgoing messages to uppercase."
# ///
"""A real Python plugin using only the SDK bundled in the IPA."""

from swiftgram import BasePlugin, Event, HookResult, HookStrategy

__permissions__ = ["outgoingMessages"]
__hooks__ = [{"event": "sendMessage", "name": "send_message"}]


class Plugin(BasePlugin):
    def on_send_message(self, event: Event) -> HookResult:
        return HookResult(HookStrategy.MODIFY, text=event.text.upper())
