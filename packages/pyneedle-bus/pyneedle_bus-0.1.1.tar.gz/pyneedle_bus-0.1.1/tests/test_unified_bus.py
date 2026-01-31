import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pytest
from needle.pointer import L
from needle.spec import RendererProtocol

# From bus
from needle.bus import (
    EventBus,
    FeedbackBus,
    LogBridge,
)

# From runtime/operators (integration test)
from needle.operators import I18NFactoryOperator, OverlayOperator


# --- Fixtures ---


class SpyRenderer(RendererProtocol):
    """A mock renderer that captures calls instead of printing."""

    def __init__(self):
        self.calls: List[Tuple[str, str, Dict[str, Any]]] = []

    def render(self, message: str, level: str = "info", **kwargs: Any) -> None:
        self.calls.append((message, level, kwargs))

    def get_last_message(self) -> str:
        return self.calls[-1][0] if self.calls else ""

    def clear(self):
        self.calls.clear()


@pytest.fixture
def mock_asset_structure(tmp_path: Path) -> Dict[str, Path]:
    """Creates a mock filesystem structure for testing i18n overlays."""
    # 1. Core App Assets (Low Priority)
    app_root = tmp_path / "app_assets"
    app_en_dir = app_root / "needle" / "en"
    app_zh_dir = app_root / "needle" / "zh"
    app_en_dir.mkdir(parents=True)
    app_zh_dir.mkdir(parents=True)

    app_en_data = {
        "welcome": "Welcome to CoreApp!",
        "setup": "Initializing system...",
    }
    app_zh_data = {
        "welcome": "欢迎使用核心应用！",
        "setup": "正在初始化系统...",
    }
    (app_en_dir / "app.json").write_text(json.dumps(app_en_data))
    (app_zh_dir / "app.json").write_text(json.dumps(app_zh_data, ensure_ascii=False))

    # 2. Plugin Assets (High Priority)
    plugin_root = tmp_path / "plugin_assets"
    plugin_en_dir = plugin_root / "needle" / "en"
    plugin_zh_dir = plugin_root / "needle" / "zh"
    plugin_en_dir.mkdir(parents=True)
    plugin_zh_dir.mkdir(parents=True)

    plugin_en_data = {
        "welcome": "Welcome from MyPlugin!",  # Override
        "farewell": "Goodbye from Plugin!",  # New
    }
    plugin_zh_data = {
        "welcome": "MyPlugin 欢迎您！",
        "farewell": "插件再见！",
    }
    (plugin_en_dir / "app.json").write_text(json.dumps(plugin_en_data))
    (plugin_zh_dir / "app.json").write_text(
        json.dumps(plugin_zh_data, ensure_ascii=False)
    )

    return {"app": app_root, "plugin": plugin_root}


# --- Test Cases ---


def test_unified_bus_integration(mock_asset_structure):
    """
    End-to-end test for the entire pyneedle-bus stack with manually assembled operators.
    """
    # 1. ARRANGE
    event_bus = EventBus()
    spy_renderer = SpyRenderer()
    feedback_bus = FeedbackBus(renderer=spy_renderer)
    bridge = LogBridge(event_bus, feedback_bus)

    # Manual Operator Assembly
    # Later roots override earlier ones? OverlayOperator uses first-match-wins.
    # So we put [Plugin, App] to let Plugin override App.
    app_factory = I18NFactoryOperator(mock_asset_structure["app"])
    plugin_factory = I18NFactoryOperator(mock_asset_structure["plugin"])

    def set_language(lang: str):
        # Build a specific overlay for the target language
        # plugin_factory(lang) returns a FileSystemOperator for that dir
        overlay = OverlayOperator([plugin_factory(lang), app_factory(lang)])
        feedback_bus.set_operator(overlay)

    # Connect the bridge
    bridge.connect(L.app.farewell, level="success")

    # 2. ACT & ASSERT: FeedbackBus direct rendering

    # Test English
    set_language("en")
    feedback_bus.info(L.app.welcome)
    assert spy_renderer.get_last_message() == "Welcome from MyPlugin!"

    # Test English - Fallback (found in App but not in Plugin)
    feedback_bus.info(L.app.setup)
    assert spy_renderer.get_last_message() == "Initializing system..."

    spy_renderer.clear()

    # Test Chinese
    set_language("zh")
    feedback_bus.warning(L.app.welcome)
    assert spy_renderer.get_last_message() == "MyPlugin 欢迎您！"
    assert spy_renderer.calls[-1][1] == "warning"

    spy_renderer.clear()

    # 3. ACT & ASSERT: EventBus -> Bridge -> FeedbackBus
    set_language("en")

    # Publish an event
    class UserLogoutEvent:
        def __init__(self, username):
            self.username = username
            self.topic = L.app.farewell

    event_bus.publish(UserLogoutEvent(username="Alice"))

    assert len(spy_renderer.calls) == 1
    assert spy_renderer.get_last_message() == "Goodbye from Plugin!"
    assert spy_renderer.calls[0][1] == "success"
