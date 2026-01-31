import asyncio
from abc import ABC, abstractmethod
from gllm_inference.realtime_session.schema import RealtimeEvent as RealtimeEvent, RealtimeState as RealtimeState

class BaseInputStreamer(ABC):
    """[BETA] A base class for input streamers.

    Attributes:
        state (RealtimeState | None): The state of the input streamer.
        input_queue (asyncio.Queue[RealtimeEvent] | None): The queue to put the input events.
    """
    state: RealtimeState | None
    input_queue: asyncio.Queue[RealtimeEvent] | None
    async def initialize(self, state: RealtimeState, input_queue: asyncio.Queue[RealtimeEvent]) -> None:
        """Initializes the input streamer.

        Args:
            input_queue (asyncio.Queue[RealtimeEvent]): The queue to put the input events.
            state (RealtimeState): The state of the input streamer.
        """
    @abstractmethod
    async def stream_input(self) -> None:
        """Streams the input from a certain source.

        This method must be implemented by subclasses to define the logic for streaming the input.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
    async def close(self) -> None:
        """Closes the input streamer.

        This method is used to close the input streamer.
        """
