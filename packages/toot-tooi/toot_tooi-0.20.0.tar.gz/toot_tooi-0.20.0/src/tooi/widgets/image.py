from pathlib import Path

from textual import getters, work
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Pretty, Static

from textual_image.widget import AutoImage, HalfcellImage, SixelImage, TGPImage, UnicodeImage

from tooi import ImageType, cache
from tooi.app import TooiApp


class RemoteImage(Widget):
    """Render an image from the web.

    Images are cached in the user cache dir.
    """

    app = getters.app(TooiApp)

    DEFAULT_CSS = """
    RemoteImage {
        height: auto;

        Image {
            height: auto;
            width: auto;
            max-height: 20;
        }
    }
    """
    path: reactive[Path | None] = reactive(None, recompose=True)
    exception: reactive[Exception | None] = reactive(None, recompose=True)

    def __init__(
        self,
        url: str,
        *,
        id: str | None = None,
        classes: str | None = None,
        blurhash: str | None = None,
        aspect_ratio: float | None = None,
    ):
        self.url = url
        self.enabled = self.app.options.image_type != ImageType.none
        super().__init__(id=id, classes=classes)

        # TODO: blurhash placeholder?
        if self.enabled:
            cache_path = cache.image_cache_path(url)
            if cache_path.exists():
                self.path = cache_path
        else:
            self.display = False

    def compose(self):
        if not self.enabled:
            return

        if self.path and (image := self.render_image(self.path)):
            yield image
        elif self.exception:
            yield Static("Error loading image:")
            yield Pretty(self.exception)
        else:
            yield Static("Loading image...")

    async def on_mount(self):
        if self.enabled and not self.path:
            self.call_after_refresh(self.fetch_image)

    @work
    async def fetch_image(self):
        try:
            self.path = await cache.download_image_cached(self.url)
        except Exception as ex:
            self.exception = ex

    def render_image(self, path: Path) -> Widget | None:
        match self.app.options.image_type:
            case None:
                return AutoImage(path)
            case ImageType.auto:
                return AutoImage(path)
            case ImageType.sixel:
                return SixelImage(path)
            case ImageType.tgp:
                return TGPImage(path)
            case ImageType.halfcell:
                return HalfcellImage(path)
            case ImageType.unicode:
                return UnicodeImage(path)
            case ImageType.none:
                return None
