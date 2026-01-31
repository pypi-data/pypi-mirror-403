from _typeshed import Incomplete
from gllm_core.event import EventEmitter
from gllm_core.schema import Event
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from gllm_inference.realtime_session.schema import RealtimeDataType as RealtimeDataType, RealtimeEvent as RealtimeEvent, RealtimeEventType as RealtimeEventType
from gllm_inference.schema import Activity as Activity, ActivityEvent as ActivityEvent
from typing import Any

class BytesEvent(Event):
    """A temporary event schema that supports bytes value.

    Attributes:
        id (str): The ID of the event. Defaults to None.
        value (str | bytes | dict[str, Any]): The value of the event. Defaults to an empty string.
        level (EventLevel): The severity level of the event. Defaults to EventLevel.INFO.
        type (str): The type of the event. Defaults to EventType.RESPONSE.
        timestamp (datetime): The timestamp of the event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the event. Defaults to an empty dictionary.
    """
    value: str | bytes | dict[str, Any]
    def serialize_value(self, value: str | bytes | dict[str, Any]) -> str | dict[str, Any]:
        """Serializes the value of the event.

        This method is used to serialize the value of the event to a string or dictionary.
        If the value is a bytes object, it will be encoded to a base64 string.
        Otherwise, the value is returned as is.

        Args:
            value (str | bytes | dict[str, Any]): The value of the event.

        Returns:
            str | dict[str, Any]: The serialized value of the event.
        """

ROLE_MAP: Incomplete

class EventOutputStreamer(BaseOutputStreamer):
    """[BETA] An event output streamer that emits output events via an event emitter.

    Attributes:
        state (RealtimeState): The state of the output streamer.
        event_emitter (EventEmitter): The event emitter to emit the output events.
    """
    event_emitter: Incomplete
    def __init__(self, event_emitter: EventEmitter) -> None:
        """Initializes the EventOutputStreamer.

        Args:
            event_emitter (EventEmitter): The event emitter to emit the output events.
        """
    async def handle(self, event: RealtimeEvent) -> None:
        """Handles the output events.

        This method is used to handle and emit the output events via the event emitter.

        Args:
            event (RealtimeEvent): The realtime events to handle.
        """
