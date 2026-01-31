from abc import ABC, abstractmethod
from gllm_inference.realtime_session.schema import RealtimeEvent as RealtimeEvent, RealtimeState as RealtimeState

class BaseOutputStreamer(ABC):
    """[BETA] A base class for output streamers.

    Attributes:
        state (RealtimeState | None): The state of the output streamer.
    """
    state: RealtimeState | None
    async def initialize(self, state: RealtimeState) -> None:
        """Initializes the output streamer.

        Args:
            state (RealtimeState): The state of the output streamer.
        """
    @abstractmethod
    async def handle(self, event: RealtimeEvent) -> None:
        """Handles output events streamed from the model.

        This method must be implemented by subclasses to define the logic for handling the output events.

        Args:
            event (RealtimeEvent): The realtime events to handle.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
    async def close(self) -> None:
        """Closes the output streamer.

        This method is used to close the output streamer.
        It is used to clean up the output streamer.
        """
