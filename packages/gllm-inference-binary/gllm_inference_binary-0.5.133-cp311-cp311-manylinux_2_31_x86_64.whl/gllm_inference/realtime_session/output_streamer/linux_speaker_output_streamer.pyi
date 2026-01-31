import asyncio
from _typeshed import Incomplete
from gllm_inference.realtime_session.constants import OutputAudioConfig as OutputAudioConfig
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from gllm_inference.realtime_session.schema import RealtimeDataType as RealtimeDataType, RealtimeEvent as RealtimeEvent, RealtimeState as RealtimeState

PLAY_CMD: Incomplete

class LinuxSpeakerOutputStreamer(BaseOutputStreamer):
    """[BETA] A Linux speaker output streamer that plays the output audio through the speakers.

    Attributes:
        state (RealtimeState): The state of the output streamer.
        play_process (asyncio.subprocess.Process | None): The process to play the output audio.
    """
    play_process: asyncio.subprocess.Process | None
    async def initialize(self, state: RealtimeState) -> None:
        """Initializes the LinuxSpeakerOutputStreamer.

        Args:
            state (RealtimeState): The state of the output streamer.

        Raises:
            OSError: If the current system is not Linux.
        """
    async def handle(self, event: RealtimeEvent) -> None:
        """Handles the output events.

        This method is used to handle the audio output events and play them through the Linux system speakers.

        Args:
            event (RealtimeEvent): The realtime events to handle.
        """
    async def close(self) -> None:
        """Closes the LinuxSpeakerOutputStreamer.

        This method is used to close the LinuxSpeakerOutputStreamer.
        It is used to clean up playing process.
        """
