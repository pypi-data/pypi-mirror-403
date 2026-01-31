from abc import ABC
from gllm_inference.realtime_session.input_streamer import KeyboardInputStreamer as KeyboardInputStreamer
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.output_streamer import ConsoleOutputStreamer as ConsoleOutputStreamer
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer

class BaseRealtimeSession(ABC):
    """[BETA] A base class for realtime session modules.

    The `BaseRealtimeSession` class provides a framework for processing real-time conversation sessions.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseRealtimeSession class."""
    async def start(self, input_streamers: list[BaseInputStreamer] | None = None, output_streamers: list[BaseOutputStreamer] | None = None) -> None:
        """Starts the real-time conversation session using the provided input and output streamers.

        This method validates the input and output streamers, and then calls the _start method.

        Args:
            input_streamers (list[BaseInputStreamer] | None, optional): The input streamers to use.
                Defaults to None.
            output_streamers (list[BaseOutputStreamer] | None, optional): The output streamers to use.
                Defaults to None.

        Raises:
            ValueError: If the `input_streamers` or `output_streamers` is an empty list.
        """
