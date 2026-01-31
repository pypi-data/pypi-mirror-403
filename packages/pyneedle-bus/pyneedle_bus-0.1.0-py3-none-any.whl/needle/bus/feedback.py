from typing import Any, Optional, Union

from needle.spec import SemanticPointerProtocol, RendererProtocol
from .store import MessageStore


class FeedbackBus:
    """
    The output channel for the application. Handles I18n lookup and rendering.
    """

    def __init__(
        self, store: MessageStore, renderer: Optional[RendererProtocol] = None
    ):
        self._store = store
        self._renderer = renderer

    def set_renderer(self, renderer: RendererProtocol) -> None:
        self._renderer = renderer

    def _get_template(self, ptr: Union[str, SemanticPointerProtocol]) -> str:
        # 1. Detect Language
        lang = self._store.detect_lang()

        # 2. Get Operator for that language
        op = self._store.get_operator(lang)

        # 3. Lookup
        template = op(ptr)

        # 4. Fallback: If not found, stringify the pointer itself
        if template is None:
            return str(ptr)

        return str(template)

    def render_to_string(
        self,
        ptr: Union[str, SemanticPointerProtocol],
        **kwargs: Any,
    ) -> str:
        """
        Resolve a template and format it into a string without rendering.

        Args:
            ptr: Semantic Pointer or string ID of the template.
            **kwargs: Arguments for template formatting.

        Returns:
            The fully formatted message string.
        """
        template = self._get_template(ptr)

        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"<formatting error for '{ptr}': missing key {e}>"
        except Exception as e:
            return f"<rendering error for '{ptr}': {e}>"

    def present(
        self,
        ptr: Union[str, SemanticPointerProtocol],
        level: str = "info",
        **kwargs: Any,
    ) -> None:
        """
        Present a message to the user via the registered renderer.

        Args:
            ptr: Semantic Pointer to the message template (e.g. L.io.file_saved)
            level: 'info', 'success', 'warning', 'error', 'debug'
            **kwargs: Arguments for template formatting
        """
        if not self._renderer:
            return

        message = self.render_to_string(ptr, **kwargs)
        self._renderer.render(message, level=level, **kwargs)

    # Convenience shortcuts

    def info(self, ptr: Union[str, SemanticPointerProtocol], **kwargs: Any) -> None:
        self.present(ptr, level="info", **kwargs)

    def success(self, ptr: Union[str, SemanticPointerProtocol], **kwargs: Any) -> None:
        self.present(ptr, level="success", **kwargs)

    def warning(self, ptr: Union[str, SemanticPointerProtocol], **kwargs: Any) -> None:
        self.present(ptr, level="warning", **kwargs)

    def error(self, ptr: Union[str, SemanticPointerProtocol], **kwargs: Any) -> None:
        self.present(ptr, level="error", **kwargs)

    def debug(self, ptr: Union[str, SemanticPointerProtocol], **kwargs: Any) -> None:
        self.present(ptr, level="debug", **kwargs)
