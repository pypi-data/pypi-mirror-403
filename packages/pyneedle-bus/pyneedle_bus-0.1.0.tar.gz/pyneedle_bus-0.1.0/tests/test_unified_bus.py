import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pytest
from needle.pointer import L
from needle.spec import RendererProtocol

# Assuming the new components are in needle.bus
from needle.bus import (
    MessageStore,
    EventBus,
    FeedbackBus,
    LogBridge,
)


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


def test_unified_bus_integration(mock_asset_structure, monkeypatch):
    """
    End-to-end test for the entire pyneedle-bus stack.
    """
    # 1. ARRANGE
    # Fresh instances for test isolation
    store = MessageStore()
    event_bus = EventBus()
    spy_renderer = SpyRenderer()
    feedback_bus = FeedbackBus(store, renderer=spy_renderer)
    bridge = LogBridge(event_bus, feedback_bus)

    # Register asset roots. Order matters: register low-priority first.
    # Our implementation gives higher priority to roots registered later.
    store.register_asset_root(mock_asset_structure["app"])
    store.register_asset_root(mock_asset_structure["plugin"])

    # Connect the bridge for zero-config logging test
    # This means any event with topic "app.farewell" will be rendered.
    bridge.connect(L.app.farewell, level="success")

    # 2. ACT & ASSERT: FeedbackBus direct rendering

    # Test English (default) - Override
    monkeypatch.setenv("NEEDLE_LANG", "en")
    feedback_bus.info(L.app.welcome)
    assert spy_renderer.get_last_message() == "Welcome from MyPlugin!"

    # Test English - Fallback
    feedback_bus.info(L.app.setup)
    assert spy_renderer.get_last_message() == "Initializing system..."

    spy_renderer.clear()

    # Test Chinese - Override
    monkeypatch.setenv("NEEDLE_LANG", "zh")
    feedback_bus.warning(L.app.welcome)
    assert spy_renderer.get_last_message() == "MyPlugin 欢迎您！"
    assert spy_renderer.calls[-1][1] == "warning"

    # Test Chinese - Fallback
    feedback_bus.info(L.app.setup)
    assert spy_renderer.get_last_message() == "正在初始化系统..."

    spy_renderer.clear()

    # Switch back to English for the final test
    monkeypatch.setenv("NEEDLE_LANG", "en")

    # 3. ACT & ASSERT: EventBus -> Bridge -> FeedbackBus

    # Publish an event. The topic L.app.farewell is connected by the bridge.
    # The event object itself can be anything.
    class UserLogoutEvent:
        def __init__(self, username):
            self.username = username
            self.topic = L.app.farewell  # Event can carry its own topic

    event_bus.publish(UserLogoutEvent(username="Alice"))

    # The bridge should have caught this and triggered the feedback bus.
    assert len(spy_renderer.calls) == 1
    # Check rendered message (using EN locale from last monkeypatch set)
    # The template for farewell is in the plugin assets for English
    assert spy_renderer.get_last_message() == "Goodbye from Plugin!"
    # Check log level
    assert spy_renderer.calls[0][1] == "success"
