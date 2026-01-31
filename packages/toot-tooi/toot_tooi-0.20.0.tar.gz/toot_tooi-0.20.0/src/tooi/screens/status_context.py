from typing import cast

from textual import getters, on, work
from textual.message import Message

from tooi.app import TooiApp
from tooi.data import accounts
from tooi.entities import Status
from tooi.goto import GotoHashtagTimeline
from tooi.messages import GotoMessage, ShowAccount, ShowHashtag
from tooi.screens.modal import ModalScreen, ModalTitle
from tooi.widgets.menu import AccountMenuItem, AcctMenuItem, Menu, MenuHeading, TagMenuItem
from tooi.widgets.status_bar import StatusBar


class StatusMenuScreen(ModalScreen[Message | None]):
    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    StatusMenuScreen {
        ListView {
            height: auto;
        }
        #hashtags,#mentions {
            margin-top: 1;
        }
    }
    """

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def compose_modal(self):
        yield ModalTitle(f"Status #{self.status.id}")
        yield Menu(*self.menu_items())
        yield StatusBar()

    def menu_items(self):
        account = self.status.account
        yield MenuHeading("Accounts:")
        yield AccountMenuItem("show_account", account)

        if self.status.reblog:
            account = self.status.reblog.account
            yield AccountMenuItem("show_account", account)

        if self.status.original.mentions:
            yield MenuHeading("Mentions:", id="mentions")
            for mention in self.status.original.mentions:
                yield AcctMenuItem("show_mention", mention.acct)

        if tags := self.status.original.tags:
            yield MenuHeading("Hashtags:", id="hashtags")
            for tag in tags:
                yield TagMenuItem("show_tag", tag)

    @on(Menu.ItemSelected)
    def on_item_selected(self, message: Menu.ItemSelected):
        message.stop()

        match message.item.code:
            case "show_account":
                item = cast(AccountMenuItem, message.item)
                self.dismiss(ShowAccount(item.account))
            case "show_tag":
                item = cast(TagMenuItem, message.item)
                self.dismiss(ShowHashtag(item.tag.name))
            case "show_mention":
                item = cast(AcctMenuItem, message.item)
                self.show_mention(item.acct)
            case _:
                pass

    @work
    async def show_mention(self, acct: str):
        status_bar = self.query_one(StatusBar)
        async with status_bar.run_with_progress("Looking up account..."):
            account = await accounts.lookup(acct)
            self.dismiss(ShowAccount(account))
