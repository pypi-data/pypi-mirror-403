from textual.events import Key
from textual.widgets import TextArea

# Keys that should be forwarded to the app for tab navigation
_TAB_NAV_KEYS = {
    "alt+1",
    "alt+2",
    "alt+3",
    "alt+4",
    "alt+5",
    "alt+6",
    "alt+7",
    "alt+8",
    "alt+9",
    "alt+left_square_bracket",
    "alt+right_square_bracket",
}


class PromptInput(TextArea):
    """TextArea that sends on Enter and inserts newlines on Shift+Enter."""

    async def _on_key(self, event: Key) -> None:
        if event.key == "enter":
            event.prevent_default()
            event.stop()
            self.post_message(PromptInput.Submitted(self))
        elif event.key == "shift+enter":
            event.prevent_default()
            event.stop()
            self.insert("\n")
        elif event.key == "ctrl+w":
            # Directly invoke app's close_tab action since TextArea captures this key
            event.prevent_default()
            event.stop()
            await self.app.action_close_tab()
        elif event.key in _TAB_NAV_KEYS:
            # Don't consume alt+number keys - let them bubble up for tab navigation
            pass
        else:
            await super()._on_key(event)

    class Submitted(TextArea.Changed):
        pass
