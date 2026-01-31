import asyncio
import re
from pathlib import Path
from threading import local
from typing import Optional

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static, TextArea
from textual_fspicker import FileOpen

from tooi.api import statuses
from tooi.app import TooiApp
from tooi.context import is_me
from tooi.data.instance import InstanceInfo
from tooi.entities import MediaAttachment, Status, StatusSource
from tooi.screens.media import AttachMediaModal
from tooi.screens.modal import ModalScreen
from tooi.widgets.compose import ComposeCharacterCount, ComposeTextArea
from tooi.widgets.form.federated_select import FederatedSelect
from tooi.widgets.form.language_select import LanguageSelect
from tooi.widgets.form.visibility_select import VisibilitySelect
from tooi.widgets.header import Header
from tooi.widgets.menu import Menu, MenuItem
from tooi.widgets.status_bar import StatusBar

# Save last dir used by the file picker
_local = local()
_local.last_picker_path = Path.home()


class ComposeScreen(ModalScreen[None]):
    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
        .label {
            padding: 0 1;
        }
        #cw_text_area {
            margin-bottom: 1;
        }
        AttachedMedia {
            height: auto;
            margin-bottom: 1;
            padding: 0 1;
        }
    }
    """

    def __init__(
        self,
        instance_info: InstanceInfo,
        in_reply_to: Optional[Status] = None,
        edit: Optional[Status] = None,
        edit_source: Optional[StatusSource] = None,
    ):
        self.instance_info = instance_info
        self.in_reply_to = in_reply_to
        self.edit = edit
        self.edit_source = edit_source
        self.attachments: list[MediaAttachment] = edit.media_attachments if edit else []

        super().__init__()

    def compose_modal(self) -> ComposeResult:
        initial_text = self._get_initial_text()
        initial_language = self._get_initial_language()
        initial_federated = self._get_initial_federated()
        initial_visibility = self._get_initial_visibility()
        initial_spoiler_text = self.edit.spoiler_text if self.edit else ""

        editing = self.edit is not None
        max_chars = self.instance_info.status_config.max_characters

        yield Header("Edit toot" if editing else "Compose toot")

        yield ComposeTextArea(
            id="compose_text_area",
            initial_text=initial_text,
            placeholder="What's on your mind?",
        )

        yield ComposeCharacterCount(initial_text, max_chars)
        yield Static("Content warning:", id="cw_label", classes="label")
        yield ComposeTextArea(
            initial_spoiler_text,
            id="cw_text_area",
            placeholder="Content warning",
        )
        yield LanguageSelect(initial_language)
        yield VisibilitySelect(initial_visibility, disabled=editing)

        if initial_federated is not None:
            yield FederatedSelect(initial_federated, disabled=editing)

        yield AttachedMedia(self.attachments)

        yield Menu(
            MenuItem("add_cw", "Add content warning", id="add_cw"),
            MenuItem("remove_cw", "Remove content warning", id="remove_cw"),
            MenuItem("attach_media", "Attach media"),
            MenuItem("post", "Edit status" if editing else "Post status"),
            MenuItem("cancel", "Cancel"),
        )

        yield StatusBar()

    def on_mount(self):
        self.compose_text_area.action_cursor_line_end()

        if self.edit and self.edit.spoiler_text:
            self.query_one("#add_cw").display = False
        else:
            self.query_one("#remove_cw").display = False
            self.query_one("#cw_label").display = False
            self.query_one("#cw_text_area").display = False

    @property
    def compose_text_area(self):
        return self.query_one("#compose_text_area", ComposeTextArea)

    @property
    def cw_text_area(self):
        return self.query_one_optional("#cw_text_area", ComposeTextArea)

    @property
    def character_count(self) -> ComposeCharacterCount:
        return self.query_one(ComposeCharacterCount)

    def on_compose_text_area_focus_next(self, message: ComposeTextArea.FocusNext):
        self.app.action_focus_next()

    def on_compose_text_area_focus_previous(self, message: ComposeTextArea.FocusPrevious):
        if message.from_id != "compose_text_area":
            self.app.action_focus_previous()

    def action_quit(self):
        self.quit_with_confirmation()

    @work
    async def quit_with_confirmation(self):
        text = self.compose_text_area.text
        content_warning = self.cw_text_area and self.cw_text_area.text

        if text or content_warning or self.attachments:
            if await self.app.confirm("Discard draft?"):
                self.app.pop_screen()
        else:
            self.app.pop_screen()

    def on_list_view_focus_previous(self):
        self.focus_previous()

    def on_text_area_changed(self, message: TextArea.Changed):
        self.character_count.update_chars(message.text_area.text)

    async def post_status(self):
        self.disable()

        if await self._post_with_progress():
            await asyncio.sleep(0.5)
            self.dismiss()
        else:
            self.enable()
            self.query_one(Menu).focus()

    async def _post_with_progress(self):
        status_bar = self.query_one(StatusBar)

        async with status_bar.run_with_progress(
            progress="Posting status...",
            error="Posting failed",
            success="Status posted",
        ):
            await self._post_or_edit_status()
            return True

        return False

    @property
    def visibility(self) -> str | None:
        return self.query_one(VisibilitySelect).selection

    @property
    def language(self) -> str | None:
        return self.query_one(LanguageSelect).selection

    @property
    def federated(self) -> bool | None:
        if select := self.query_one_optional(FederatedSelect):
            return select.selection

    async def _post_or_edit_status(self):
        spoiler_text = self.cw_text_area.text if self.cw_text_area else None
        in_reply_to = self.in_reply_to.original.id if self.in_reply_to else None
        media_ids = [a.id for a in self.attachments] if self.attachments else None

        if self.edit:
            await statuses.edit(
                self.edit.id,
                self.compose_text_area.text,
                spoiler_text=spoiler_text,
                media_ids=media_ids,
                language=self.language,
            )
        else:
            await statuses.post(
                self.compose_text_area.text,
                visibility=self.visibility,
                spoiler_text=spoiler_text,
                in_reply_to=in_reply_to,
                local_only=not self.federated,
                media_ids=media_ids,
                language=self.language,
            )

    def disable(self):
        self.compose_text_area.disabled = True
        self.query_one(Menu).disabled = True

    def enable(self):
        self.compose_text_area.disabled = False
        self.query_one(Menu).disabled = False

    async def on_menu_item_selected(self, message: Menu.ItemSelected):
        match message.item.code:
            case "post":
                asyncio.create_task(self.post_status())
            case "add_cw":
                self.add_content_warning()
            case "attach_media":
                self.attach_media()
            case "remove_cw":
                self.remove_content_warning()
            case "cancel":
                self.dismiss()
            case _:
                pass

    @work
    async def attach_media(self):
        path = await self.app.push_screen_wait(FileOpen(_local.last_picker_path))
        if not path:
            return

        if path.is_file() and path.exists():
            _local.last_picker_path = path.parent

        media = await self.app.push_screen_wait(AttachMediaModal(path))
        if not media:
            return

        # TODO: connect these two using data binding?
        # https://textual.textualize.io/guide/reactivity/#data-binding
        self.attachments.append(media.attachment)
        attached_media = self.query_one(AttachedMedia)
        attached_media.attachments = self.attachments
        attached_media.mutate_reactive(AttachedMedia.attachments)

    def add_content_warning(self):
        self.query_one("#add_cw", MenuItem).hide()
        self.query_one("#remove_cw", MenuItem).show()

        self.query_one("#cw_label").display = True
        cw_text_area = self.query_one("#cw_text_area")
        cw_text_area.display = True
        cw_text_area.focus()

    def remove_content_warning(self):
        self.query_one("#add_cw", MenuItem).show()
        self.query_one("#remove_cw", MenuItem).hide()

        self.query_one("#cw_label").display = False
        cw_text_area = self.query_one("#cw_text_area", ComposeTextArea)
        cw_text_area.display = False
        cw_text_area.clear()

    # TODO: When replying to multiple users, put the parent post author first,
    # then have the other mentions be initially selected so it's easy to discard
    # them by just starting typing.
    def _get_initial_text(self) -> str:
        if self.edit:
            return self.edit_source.text if self.edit_source else ""

        if self.in_reply_to:
            status = self.in_reply_to.original
            author = status.account.acct
            mentions = [m.acct for m in status.mentions]

            reply_tos: set[str] = set()
            for acct in [author, *mentions]:
                if not is_me(acct):
                    reply_tos.add(acct)

            return " ".join([f"@{acct}" for acct in reply_tos]) + " "

        return ""

    def _get_initial_language(self) -> str:
        if self.edit and self.edit.language:
            return self.edit.language

        return self.instance_info.get_default_language()

    def _get_initial_visibility(self) -> str:
        if self.edit:
            return self.edit.visibility

        if self.in_reply_to:
            return self.in_reply_to.original.visibility

        return self.instance_info.get_default_visibility()

    def _get_initial_federated(self) -> bool | None:
        if self.edit and self.edit.local_only is not None:
            return not self.edit.local_only

        if self.in_reply_to and self.in_reply_to.local_only is not None:
            return not self.in_reply_to.local_only

        return self.instance_info.get_federated()


class AttachedMedia(Vertical):
    attachments: reactive[list[MediaAttachment]] = reactive([], recompose=True)

    def __init__(self, initial_attachments: list[MediaAttachment]):
        super().__init__()
        self.attachments = initial_attachments

    def compose(self):
        if not self.attachments:
            return

        yield Static("[bold]Attached media:[/bold]")
        for attachment in self.attachments:
            description = re.sub(r"\s+", " ", attachment.description or "").strip()
            if description:
                yield Static(f"#{attachment.id}: [dim]{description}[/]")
            else:
                yield Static(f"#{attachment.id}")
