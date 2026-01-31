from datetime import date

from textual import getters, on, work
from textual.containers import Vertical
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Link, Rule, Static

from tooi.app import TooiApp
from tooi.data import tags
from tooi.entities import Tag
from tooi.goto import GotoHashtagTimeline
from tooi.messages import GotoMessage
from tooi.screens.modal import ModalScreen, ModalTitle
from tooi.utils.charts import date_bar_chart
from tooi.utils.string import bool_markup
from tooi.widgets.menu import Menu, MenuItem
from tooi.widgets.status_bar import StatusBar


class HashtagDetailsModal(ModalScreen[Message | None]):
    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    HashtagDetailsModal {
        HashtagDetails {
            height: auto;
        }
        Menu,HashtagDetails {
            margin-top: 1;
        }
    }
    """

    tag: reactive[Tag | None] = reactive(None)

    def __init__(self, tag_name: str):
        super().__init__()
        self.tag_name = tag_name

    def compose_modal(self):
        yield ModalTitle(f"Hashtag #{self.tag_name}")
        yield HashtagDetails().data_bind(HashtagDetailsModal.tag)

        yield Menu(
            MenuItem("show_timeline", "Show timeline"),
            MenuItem("toggle_following", "(Un)follow"),
            MenuItem("toggle_featured", "(Un)feature"),
        )

        yield StatusBar()

    @work
    async def on_mount(self):
        status_bar = self.query_one(StatusBar)
        async with status_bar.run_with_progress("Looking up tag..."):
            import asyncio
            await asyncio.sleep(1)
            self.tag = await tags.get(self.tag_name)

    @on(Menu.ItemSelected)
    def on_item_selected(self, message: Menu.ItemSelected):
        message.stop()

        match message.item.code:
            case "show_timeline":
                self.dismiss(GotoMessage(GotoHashtagTimeline(self.tag_name)))
            case "toggle_following":
                self.toggle_following()
            case "toggle_featured":
                self.toggle_featured()
            case _:
                pass

    @work
    async def toggle_following(self):
        assert self.tag is not None
        status_bar = self.query_one(StatusBar)
        if self.tag.following:
            async with status_bar.run_with_progress("Unfollowing..."):
                self.tag = await tags.unfollow(self.tag_name)
        else:
            async with status_bar.run_with_progress("Following..."):
                self.tag = await tags.follow(self.tag_name)

    @work
    async def toggle_featured(self):
        assert self.tag is not None
        status_bar = self.query_one(StatusBar)
        if self.tag.featuring:
            async with status_bar.run_with_progress("Unfeaturing..."):
                self.tag = await tags.unfeature(self.tag_name)
        else:
            async with status_bar.run_with_progress("Featuring..."):
                self.tag = await tags.feature(self.tag_name)


class HashtagDetails(Vertical):
    DEFAULT_CSS = """
    HashtagDetails {
        .loading {
            height: 13;
            content-align: center middle;
            color: $text-muted;
        }
        #chart,#chart-title {
            content-align-horizontal: center;
        }
    }
    """
    tag: reactive[Tag | None] = reactive(None, recompose=True)

    def compose(self):
        if self.tag:
            yield Static("[bold]History[/bold]", id="chart-title")
            yield Static(self.hashtag_chart(self.tag), id="chart")
            yield Rule()
            yield Static(f"Following: {bool_markup(self.tag.following)}")
            yield Static(f"Featured: {bool_markup(self.tag.featuring)}")
            yield Link(self.tag.url)
        else:
            yield Static("Loading...", classes="loading")

    def hashtag_chart(self, tag: Tag) -> Content:
        history = list(reversed(tag.history))
        dates = [date.fromtimestamp(int(h.day)) for h in history]
        values = [int(h.uses) for h in history]
        return date_bar_chart(dates, values)
