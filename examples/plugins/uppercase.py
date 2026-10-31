"""A real Python plugin using only the SDK bundled in the IPA."""

from swiftgram import BasePlugin, Event, HookResult, HookStrategy

__id__ = "uppercase"
__name__ = "Uppercase composed messages"
__version__ = "1.0"
__permissions__ = ["outgoingMessages"]
__hooks__ = [{"event": "sendMessage", "name": "send_message"}]


class Plugin(BasePlugin):
    def on_send_message(self, event: Event) -> HookResult:
        return HookResult(HookStrategy.MODIFY, text=event.text.upper())
