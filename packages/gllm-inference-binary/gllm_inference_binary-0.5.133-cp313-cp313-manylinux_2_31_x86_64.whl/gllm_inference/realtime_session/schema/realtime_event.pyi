from enum import StrEnum
from pydantic import BaseModel
from typing import Any

class RealtimeEventType(StrEnum):
    """[BETA] Defines the event types for the realtime session."""
    ACTIVITY: str
    INPUT: str
    OUTPUT: str

class RealtimeDataType(StrEnum):
    """[BETA] Defines the data types for the realtime session."""
    AUDIO: str
    IMAGE: str
    TEXT: str

class RealtimeActivityType(StrEnum):
    """[BETA] Defines common realtime activity types of the realtime session."""
    INTERRUPTION: str
    TERMINATION: str
    TEXT_COMPLETE: str
    TOOL_CALL: str
    TOOL_CALL_COMPLETE: str

class RealtimeEvent(BaseModel):
    """[BETA] Defines the realtime event schemas for the realtime session.

    Attributes:
        type (RealtimeEventType): The type of the event.
        data (str | bytes): The data of the event.
        data_type (RealtimeDataType): The data type of the event.
        metadata (dict[str, Any]): The metadata of the event.
    """
    type: RealtimeEventType
    data: str | bytes
    data_type: RealtimeDataType
    metadata: dict[str, Any]
    @classmethod
    def activity(cls, activity: str, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an activity event.

        Args:
            activity (str): The activity of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The activity event.
        """
    @classmethod
    def input_text(cls, text: str, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an input text event.

        Args:
            text (str): The text of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The input text event.
        """
    @classmethod
    def output_text(cls, text: str, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an output text event.

        Args:
            text (str): The text of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The output text event.
        """
    @classmethod
    def input_audio(cls, audio: bytes, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an input audio event.

        Args:
            audio (bytes): The audio of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The input audio event.
        """
    @classmethod
    def output_audio(cls, audio: bytes, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an output audio event.

        Args:
            audio (bytes): The audio of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The output audio event.
        """
    @classmethod
    def input_image(cls, image: bytes, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an input image event.

        Args:
            image (bytes): The image of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The input image event.
        """
    @classmethod
    def output_image(cls, image: bytes, metadata: dict[str, Any] | None = None) -> RealtimeEvent:
        """Create an output image event.

        Args:
            image (bytes): The image of the event.
            metadata (dict[str, Any], optional): The metadata of the event. Defaults to None.

        Returns:
            RealtimeEvent: The output image event.
        """
