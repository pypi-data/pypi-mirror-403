from .event import EventBus, EventHandler
from .feedback import FeedbackBus
from .bridge import LogBridge

__all__ = [
    "EventBus",
    "EventHandler",
    "FeedbackBus",
    "LogBridge",
    "bus",  # The default FeedbackBus singleton
    "event_bus",  # The default EventBus singleton
]

# --- Default Singleton Instances ---
# For simple apps (like CLI tools), a global singleton is often sufficient.
# Complex apps (like Cascade Engine) may instantiate their own buses.

# Note: Renderer and Operator are not set by default.
# The application entry point (CLI/Main) must call:
# - `bus.set_renderer(...)`
# - `bus.set_operator(...)`
bus = FeedbackBus()

event_bus = EventBus()
