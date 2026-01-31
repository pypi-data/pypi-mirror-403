from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.schema import RealtimeEvent as RealtimeEvent

class EventInputStreamer(BaseInputStreamer):
    """[BETA] An input streamer that processes pushed input events.

    Attributes:
        state (RealtimeState): The state of the input streamer.
        input_queue (asyncio.Queue[RealtimeEvent]): The queue to put the input events.
    """
    async def stream_input(self) -> None:
        """Streams the input events.

        This method is intentionally left blank as the input events are pushed to the input queue by the `push` method.
        """
    def push(self, event: RealtimeEvent) -> None:
        """Pushes an input event to the input queue.

        This method is used to push an input event to the input queue.

        Args:
            event (RealtimeEvent): The event to push.
        """
