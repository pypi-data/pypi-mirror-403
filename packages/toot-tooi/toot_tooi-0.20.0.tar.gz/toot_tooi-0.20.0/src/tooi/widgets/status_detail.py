from rich.console import RenderableType
from textual import getters, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Link as TLink

from tooi.app import TooiApp
from tooi.data.statuses import translate
from tooi.entities import MediaAttachment, Status, Translation, TranslationAttachment
from tooi.utils.classes import class_dict
from tooi.utils.datetime import format_datetime
from tooi.widgets.account import AccountHeader
from tooi.widgets.image import RemoteImage
from tooi.widgets.link import Link
from tooi.widgets.markdown import Markdown
from tooi.widgets.poll import Poll
from tooi.widgets.status_bar import StatusBar


class StatusDetail(Widget):
    app = getters.app(TooiApp)

    _revealed: set[str] = set()
    _translated: dict[str, Translation] = {}

    DEFAULT_CSS = """
    StatusDetail {
        height: auto;

        .status_content {
            margin-top: 1;
        }

        .spoiler_text {
            margin-top: 1;
        }

        .sensitive_content {
            height: auto;
        }

        StatusSensitiveNotice { display: none; }

        &.hide_sensitive {
            .sensitive_content { display: none; }
            StatusSensitiveNotice { display: block; }
            StatusSensitiveOpenedNotice { display: none; }
        }
    }
    """

    translation: reactive[Translation | None] = reactive(None, recompose=True)

    def __init__(self, status: Status):
        super().__init__()
        self.status = status
        self.sensitive = self.status.original.sensitive
        self.set_class(self.sensitive and not self.revealed, "hide_sensitive")

    def reveal(self):
        status_id = self.status.original.id
        if status_id in self._revealed:
            self._revealed.discard(status_id)
        else:
            self._revealed.add(status_id)

        self.set_class(self.sensitive and not self.revealed, "hide_sensitive")

    @work
    async def translate(self):
        status_id = self.status.original.id

        if self.translation:
            self.translation = None
        elif status_id in self._translated:
            self.translation = self._translated[status_id]
        else:
            status_bar = self.screen.query_one(StatusBar)
            async with status_bar.run_with_progress("Translating..."):
                translation = await translate(status_id)
                self._translated[status_id] = translation
                self.translation = translation

    @property
    def revealed(self) -> bool:
        show_preference = self.app.instance.get_always_show_sensitive()
        show_option = self.app.options.always_show_sensitive
        return show_preference or show_option or self.status.original.id in self._revealed

    def compose(self) -> ComposeResult:
        status = self.status.original
        translation = self.translation
        translated_poll = translation.poll if translation else None
        translated_attachments = translation.media_attachments if translation else None
        spoiler_text = translation.spoiler_text if translation else status.spoiler_text
        content_md = translation.content_md if translation else status.content_md

        if self.status.reblog:
            yield StatusHeader(f"boosted by {self.status.account.acct}")

        if acct := self._get_in_reply_to_account(status):
            yield StatusHeader(f"in reply to {acct}")

        yield AccountHeader(status.account)

        if spoiler_text:
            yield Static(spoiler_text, markup=False, classes="spoiler_text")

        if status.sensitive:
            yield StatusSensitiveNotice()
            yield StatusSensitiveOpenedNotice()

        # Content which should be hidden if status is sensitive and not revealed
        with Vertical(classes="sensitive_content"):
            yield Markdown(content_md, classes="status_content")

            if status.poll:
                yield Poll(status.poll, translated_poll)

            if status.card:
                yield StatusCard(status)

            for idx, attachment in enumerate(status.original.media_attachments):
                translated_attachment = (
                    translated_attachments[idx] if translated_attachments else None
                )
                yield StatusMediaAttachment(attachment, translated_attachment)

        yield StatusMeta(status)

        if t := self.translation:
            from_ = t.detected_source_language
            yield Static(f"[grey]Translated from [bold]{from_}[bold] to {t.language} by {t.provider}[/grey]")

    def _get_in_reply_to_account(self, status: Status) -> str | None:
        if status.in_reply_to_account_id == status.account.id:
            return status.account.acct

        for mention in status.mentions:
            if mention.id == status.in_reply_to_account_id:
                return mention.acct

        return None


class StatusHeader(Static):
    DEFAULT_CSS = """
    StatusHeader {
        color: gray;
        border-bottom: ascii gray;
    }
    """

    def __init__(self, renderable: RenderableType = ""):
        super().__init__(renderable, markup=False)


class StatusCard(Widget):
    DEFAULT_CSS = """
    StatusCard {
        border: round white;
        padding: 0 1;
        height: auto;
        margin-top: 1;

        .title {
            text-style: bold;
        }
    }

    """

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def compose(self):
        card = self.status.original.card

        if not card:
            return

        yield Link(card.url, card.title, classes="title")

        if card.author_name:
            yield Static(f"by {card.author_name}", markup=False)

        if card.description:
            yield Static("")
            yield Static(card.description, markup=False)

        if card.image:
            yield RemoteImage(card.image)

        yield TLink(card.url)


class StatusMediaAttachment(Widget):
    DEFAULT_CSS = """
    StatusMediaAttachment {
        border-top: ascii gray;
        height: auto;

        .title {
            text-style: bold;
        }

        .media_image {
            margin: 1 0;
        }
    }
    """

    def __init__(
        self, attachment: MediaAttachment, translated_attachment: TranslationAttachment | None
    ):
        self.attachment = attachment
        self.translated_attachment = translated_attachment
        super().__init__()

    def compose(self):
        yield Static(f"Media attachment ({self.attachment.type})", markup=False, classes="title")

        description = (
            self.translated_attachment.description
            if self.translated_attachment
            else self.attachment.description
        )
        if description:
            yield Static(description, markup=False)

        if self.attachment.type == "image":
            yield RemoteImage(
                self.attachment.preview_url,
                blurhash=self.attachment.blurhash,
                aspect_ratio=self.attachment.aspect_ratio,
                classes="media_image",
            )

        yield Link(self.attachment.url)


class StatusMeta(Widget):
    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    StatusMeta {
        color: gray;
        border-top: ascii gray;
        layout: horizontal;
        height: auto;

        .highlighted {
            color: $accent;
        }
    }

    StatusMeta > * {
        width: auto;
    }
    """

    status: reactive[Status | None] = reactive(None, recompose=True)

    def __init__(self, status: Status):
        super().__init__()
        self.status = status

    def visibility_string(self, status: Status):
        vis = f"{status.visibility.capitalize()}"
        if status.local_only:
            vis += " (local only)"
        return vis

    def format_timestamp(self, status: Status):
        relative = self.app.options.relative_timestamps
        created_ts = format_datetime(status.created_at, relative=relative)

        if status.edited_at:
            edited_ts = format_datetime(status.edited_at, relative=relative)
            return f"{created_ts} (edited {edited_ts} ago)"

        return created_ts

    def compose(self):
        status = self.status
        if not status:
            return

        original = status.original

        yield Static(self.format_timestamp(status), markup=False, classes="timestamp")
        yield Static(" · ")

        yield Static(
            f"{original.reblogs_count} boosts",
            markup=False,
            classes=class_dict(highlighted=status.reblogged),
        )
        yield Static(" · ")
        yield Static(
            f"{original.favourites_count} favourites",
            markup=False,
            classes=class_dict(highlighted=status.favourited),
        )
        yield Static(" · ")
        yield Static(f"{original.replies_count} replies", markup=False)
        yield Static(" · ")
        yield Static(self.visibility_string(original), markup=False)
        if original.language:
            yield Static(" · ")
            yield Static(original.language, markup=False)


class StatusSensitiveNotice(Static):
    DEFAULT_CSS = """
    StatusSensitiveNotice {
        margin-top: 1;
        padding-left: 1;
        color: red;
        border: round red;
    }
    """

    def __init__(self):
        super().__init__("Marked as sensitive. Press S to view.")


class StatusSensitiveOpenedNotice(Static):
    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    StatusSensitiveOpenedNotice {
        margin-top: 1;
        padding-left: 1;
        color: gray;
        border: round gray;
    }
    """

    def __init__(self):
        label = "Marked as sensitive."
        if not self.app.options.always_show_sensitive:
            label += " Press S to hide."
        super().__init__(label)
