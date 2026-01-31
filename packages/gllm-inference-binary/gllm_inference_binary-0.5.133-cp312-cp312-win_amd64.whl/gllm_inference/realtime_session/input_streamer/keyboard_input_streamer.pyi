import asyncio
from _typeshed import Incomplete
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.schema import RealtimeActivityType as RealtimeActivityType, RealtimeEvent as RealtimeEvent, RealtimeState as RealtimeState

DEFAULT_QUIT_CMD: str

class KeyboardInputStreamer(BaseInputStreamer):
    """[BETA] A keyboard input streamer that reads the input text from the keyboard.

    This implementation uses prompt_toolkit for async input reading, which avoids
    zombie threads and provides better cancellation behavior compared to
    asyncio.to_thread().

    Attributes:
        state (RealtimeState): The state of the input streamer.
        input_queue (asyncio.Queue[RealtimeEvent]): The queue to put the input events.
        quit_cmd (str): The command to quit the conversation.
    """
    record_process: asyncio.subprocess.Process | None
    quit_cmd: Incomplete
    def __init__(self, quit_cmd: str = ...) -> None:
        """Initializes the KeyboardInputStreamer.

        Args:
            quit_cmd (str, optional): The command to quit the conversation. Defaults to DEFAULT_QUIT_CMD.
        """
    async def initialize(self, state: RealtimeState, input_queue: asyncio.Queue[RealtimeEvent]) -> None:
        """Initializes the input streamer.

        Args:
            input_queue (asyncio.Queue[RealtimeEvent]): The queue to put the input events.
            state (RealtimeState): The state of the input streamer.
        """
    async def stream_input(self) -> None:
        """Streams the input from the keyboard.

        This method is used to stream the input text from the keyboard to the input queue.

        Raises:
            AttributeError: If input streamer is not initialized.
            asyncio.CancelledError: If termination is detected or quit command is entered.
        """
    async def close(self) -> None:
        """Closes the input streamer.

        This method is used to close the input streamer.
        """
