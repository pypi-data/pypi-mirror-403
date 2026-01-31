from typing import Any, Type, Union

from needle.spec import SemanticPointerProtocol
from .event import EventBus
from .feedback import FeedbackBus


class LogBridge:
    """
    Connects the EventBus (Logic) to the FeedbackBus (Presentation).

    It listens for events and attempts to render them using the FeedbackBus.
    This enables 'Zero-Config Logging' if the Event Topic matches an I18n Key.
    """

    def __init__(self, event_bus: EventBus, feedback_bus: FeedbackBus):
        self.event_bus = event_bus
        self.feedback_bus = feedback_bus

    def connect(
        self,
        topic: Union[str, SemanticPointerProtocol, Type[Any]],
        ptr: Union[str, SemanticPointerProtocol, None] = None,
        level: str = "info",
    ) -> None:
        """
        Explicitly map an Event Topic to a Feedback Pointer.

        Args:
            topic: The event topic to listen for.
            ptr: The I18n pointer to use for rendering.
                 If None, assumes topic IS the pointer (Auto-Bridge).
            level: The log level.
        """
        target_ptr: Union[str, SemanticPointerProtocol]

        if ptr is not None:
            # Explicit mapping always wins.
            target_ptr = ptr
        elif not isinstance(topic, type):
            # Auto-bridge for string/pointer topics.
            target_ptr = topic
        else:
            # A type-based topic was given without an explicit pointer. This is an error.
            raise TypeError(
                f"Cannot auto-bridge event type '{getattr(topic, '__name__', 'UnknownType')}'. "
                "An explicit 'ptr' (SemanticPointer) must be provided when connecting a type-based topic."
            )

        def handler(event: Any):
            # Extract data for template formatting
            data = {}
            if isinstance(event, dict):
                data = event
            elif hasattr(event, "__dict__"):
                data = event.__dict__

            # If the event payload is nested (like Cascade GenericEventIR),
            # we might want to flatten it or pass specific parts.
            # For now, we pass the whole object structure and let format() access attributes.
            # e.g. "{payload.task_id}"

            self.feedback_bus.present(target_ptr, level=level, **data)

        self.event_bus.subscribe(topic, handler)
