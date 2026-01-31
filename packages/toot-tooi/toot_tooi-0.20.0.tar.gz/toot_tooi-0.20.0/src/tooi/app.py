import asyncio
import shlex
from pathlib import Path
from typing_extensions import override

from textual import on, work
from textual.app import App
from textual.screen import ModalScreen

from tooi import __version__, http, messages
from tooi.asyncio import create_async_context, set_async_context
from tooi.cache import download_images_cached
from tooi.commands import TooiCommandsProvider
from tooi.credentials import activate_account, load_credentials
from tooi.data.accounts import verify_credentials
from tooi.data.instance import get_instance_info
from tooi.screens.loading import LoadingScreen
from tooi.settings import Options, get_stylesheet_path
from tooi.widgets.dialog import ConfirmationDialog


class TooiApp(App[None]):
    TITLE = "tooi"
    SUB_TITLE = __version__
    SCREENS = {"loading": LoadingScreen}
    CSS_PATH = "app.css"
    COMMANDS = App.COMMANDS | {TooiCommandsProvider}

    BINDINGS = [
        ("q", "pop_or_quit", "Quit"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self, options: Options):
        base_css = Path("./app.css")
        user_css = get_stylesheet_path()
        css_path = [base_css, user_css] if user_css.exists() else [base_css]
        super().__init__(css_path=css_path)  # type: ignore

        self.options = options
        set_async_context(create_async_context(self))

    @override
    async def _shutdown(self) -> None:
        await super()._shutdown()
        await http.close_session()

    @work
    async def on_mount(self):
        from tooi.screens.accounts_screen import AccountsScreen

        credentials = load_credentials()
        if not credentials.active_acct:
            if acct := await self.push_screen_wait(AccountsScreen()):
                await activate_account(acct)
            else:
                self.exit()

        self.push_screen("loading")
        self.load_initial_data()

    @work
    async def load_initial_data(self):
        from tooi.screens.main import MainScreen
        from tooi.screens.error_box import ErrorBox

        instance, account = await asyncio.gather(
            get_instance_info(),
            verify_credentials(),
            return_exceptions=True,
        )

        if isinstance(instance, BaseException):
            modal = ErrorBox("Failed fetching instance info", None, instance)
            await self.push_screen_wait(modal)
            self.open_accounts_screen(quit_on_dismiss=True)
            return

        if isinstance(account, BaseException):
            modal = ErrorBox("Failed authenticating account", None, account)
            await self.push_screen_wait(modal)
            self.open_accounts_screen(quit_on_dismiss=True)
            return

        self.instance = instance
        self.switch_screen(MainScreen(instance, account))  # type: ignore (not sure why this errors)

    @work
    async def open_accounts_screen(self, quit_on_dismiss: bool = False):
        from tooi.screens.accounts_screen import AccountsScreen

        if acct := await self.push_screen_wait(AccountsScreen()):
            self.switch_screen(LoadingScreen())  # type: ignore (not sure why this errors)
            await activate_account(acct)
            self.load_initial_data()
        elif quit_on_dismiss:
            self.exit()

    async def confirm(
        self,
        title: str,
        *,
        text: str | None = None,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> bool:
        dialog = ConfirmationDialog(
            modal_title=title,
            modal_text=text,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
        )
        return await self.push_screen_wait(dialog)

    def show_error_modal(
        self,
        message: str | None = None,
        title: str = "Error",
        ex: Exception | None = None,
    ):
        """Open a modal screen with an error."""
        from tooi.screens.error_box import ErrorBox

        self.push_screen(ErrorBox(title, message, ex))

    async def show_error_modal_wait(
        self,
        message: str | None = None,
        title: str = "Error",
        ex: Exception | None = None,
    ):
        """Open a modal screen with an error and wait for it to be dismissed."""
        from tooi.screens.error_box import ErrorBox

        await self.push_screen_wait(ErrorBox(title, message, ex))

    @work
    async def action_pop_or_quit(self):
        if len(self.screen_stack) > 2:
            self.pop_screen()
        else:
            if await self.confirm("Quit tooi?", confirm_label="Quit"):
                self.exit()

    def action_show_help(self):
        if self.screen.query("HelpPanel"):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()

    def close_modals(self):
        while isinstance(self.screen, ModalScreen):
            self.pop_screen()

    def on_show_images(self, message: messages.ShowImages):
        if message.media_attachments:
            image_viewer = self.options.image_viewer
            if image_viewer:
                urls = [m.url for m in message.media_attachments]
                self._show_images(image_viewer, urls)
            else:
                from tooi.widgets.gallery import GalleryScreen

                self.push_screen(GalleryScreen(message.media_attachments))

    @work
    async def _show_images(self, image_viewer: str, urls: list[str]):
        """
        Open a local image viewer to display the given images, which should be a list of URLs.
        This returns immediately and starts the work in a background thread.
        """
        paths = await download_images_cached(urls)
        args = [image_viewer] + [str(p) for p in paths]
        cmd = shlex.join(args)

        # Spawn the image viewer.
        process = await asyncio.create_subprocess_shell(cmd)
        # ... and wait for it to exit.
        await process.communicate()

    @on(messages.FocusNext)
    def on_focus_next(self):
        self.screen.focus_next()

    @on(messages.FocusPrevious)
    def on_focus_previous(self):
        self.screen.focus_previous()
