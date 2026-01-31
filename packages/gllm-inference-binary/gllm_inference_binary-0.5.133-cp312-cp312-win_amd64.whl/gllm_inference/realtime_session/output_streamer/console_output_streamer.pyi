from gllm_inference.realtime_session.output_streamer.event_output_streamer import EventOutputStreamer as EventOutputStreamer
from gllm_inference.realtime_session.schema import RealtimeDataType as RealtimeDataType, RealtimeEvent as RealtimeEvent

class ConsoleOutputStreamer(EventOutputStreamer):
    """[BETA] A console output streamer that prints the output to the console.

    Attributes:
        state (RealtimeState): The state of the output streamer.
        event_emitter (EventEmitter): The event emitter to print the output to the console.
    """
    def __init__(self) -> None:
        """Initializes the ConsoleOutputStreamer."""
    async def handle(self, event: RealtimeEvent) -> None:
        """Handles the output events.

        This method is used to handle and print the output events to the console.

        Args:
            event (RealtimeEvent): The realtime events to handle.
        """
