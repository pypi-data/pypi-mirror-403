from .event import EventBus, EventHandler
from .feedback import FeedbackBus
from .store import MessageStore
from .bridge import LogBridge

__all__ = [
    "EventBus",
    "EventHandler",
    "FeedbackBus",
    "MessageStore",
    "LogBridge",
    "bus",  # The default FeedbackBus singleton
    "event_bus",  # The default EventBus singleton
    "message_store",  # The default Store
]

# --- Default Singleton Instances ---
# For simple apps (like CLI tools), a global singleton is often sufficient.
# Complex apps (like Cascade Engine) may instantiate their own buses.

message_store = MessageStore()

# Note: Renderer is not set by default.
# The application entry point (CLI/Main) must call `bus.set_renderer(...)`
bus = FeedbackBus(store=message_store)

event_bus = EventBus()
