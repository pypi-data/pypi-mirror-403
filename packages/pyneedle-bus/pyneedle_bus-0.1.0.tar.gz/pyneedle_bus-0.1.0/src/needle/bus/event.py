from collections import defaultdict
from typing import Any, Callable, Dict, List, Type, Union

from needle.spec import SemanticPointerProtocol

# Type alias for event handlers
# Handlers receive the raw event object (or Dict if published as dict)
EventHandler = Callable[[Any], None]


class EventBus:
    """
    A high-performance, in-memory event bus supporting Semantic Pointer routing.
    """

    def __init__(self):
        # Mapping: Topic String -> List of Handlers
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        # Mapping: Event Type (Class) -> List of Handlers
        self._type_subscribers: Dict[Type[Any], List[EventHandler]] = defaultdict(list)
        # Wildcard or special pattern subscribers could be added here

    def subscribe(
        self,
        topic: Union[str, SemanticPointerProtocol, Type[Any]],
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to events.

        Args:
            topic: Can be:
                   - A Semantic Pointer (L.run.started) -> converted to string "run.started"
                   - A string ("run.started")
                   - A Class (RunStartedEvent) -> for type-based dispatch
            handler: Function to call when event occurs.
        """
        if isinstance(topic, type):
            self._type_subscribers[topic].append(handler)
        else:
            # Normalize pointer/string to string key
            key = str(topic)
            self._subscribers[key].append(handler)

    def publish(
        self, event: Any, topic: Union[str, SemanticPointerProtocol, None] = None
    ) -> None:
        """
        Dispatch an event to subscribers.

        Args:
            event: The event object (dataclass, dict, etc.)
            topic: Optional override for the topic.
                   If event has a 'topic' attribute or key, that is used by default.
                   If event is a SemanticPointer, it is treated as a signal (topic=event, data={}).
        """
        # 1. Determine the topic string
        resolved_topic: str = ""

        if topic:
            resolved_topic = str(topic)
        elif hasattr(event, "topic"):
            resolved_topic = str(event.topic)
        elif isinstance(event, dict) and "topic" in event:
            resolved_topic = str(event["topic"])
        elif hasattr(event, "__str__") and not hasattr(event, "__dict__"):
            # Edge case: publishing a bare SemanticPointer as a signal
            resolved_topic = str(event)

        # 2. Dispatch by Topic (String matching)
        if resolved_topic:
            handlers = self._subscribers.get(resolved_topic)
            if handlers:
                for handler in handlers:
                    handler(event)

        # 3. Dispatch by Type (Class matching)
        # This allows Cascade-style typed events: bus.publish(RunStarted(...))
        event_type = type(event)
        type_handlers = self._type_subscribers.get(event_type)
        if type_handlers:
            for handler in type_handlers:
                handler(event)

        # Future: Add wildcard matching (e.g. "run.*") if needed.
