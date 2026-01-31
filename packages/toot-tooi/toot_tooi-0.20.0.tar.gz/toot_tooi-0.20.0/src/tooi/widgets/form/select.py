from textual import getters, widgets
from textual.binding import Binding
from textual.types import SelectType

from tooi.app import TooiApp


class Select(widgets.Select[SelectType]):
    """Extend Select to modify bindings"""

    app = getters.app(TooiApp)

    BINDINGS = [
        Binding("enter,space", "show_overlay", "Show menu", show=False),
        Binding("up,k", "focus_previous", "Move up", show=False),
        Binding("down,j", "focus_next", "Move down", show=False),
    ]

    def action_focus_next(self):
        self.app.screen.focus_next()

    def action_focus_previous(self):
        self.app.screen.focus_previous()
