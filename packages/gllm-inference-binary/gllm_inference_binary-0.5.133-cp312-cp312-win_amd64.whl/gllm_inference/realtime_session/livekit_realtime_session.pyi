import asyncio
import logging
from _typeshed import Incomplete
from gllm_inference.realtime_session.constants import InputAudioConfig as InputAudioConfig, NoiseThreshold as NoiseThreshold, OutputAudioConfig as OutputAudioConfig
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from gllm_inference.realtime_session.realtime_session import BaseRealtimeSession as BaseRealtimeSession
from gllm_inference.realtime_session.schema import RealtimeActivityType as RealtimeActivityType, RealtimeDataType as RealtimeDataType, RealtimeEvent as RealtimeEvent, RealtimeEventType as RealtimeEventType, RealtimeState as RealtimeState
from livekit import rtc

class Key:
    """Defines valid keys in LiveKit Realtime Session."""
    INPUT_AUDIO: str
    LK_TRANSCRIPTION: str
    LK_TRANSCRIPTION_FINAL: str
    TRACK_SUBSCRIBED: str
    TRUE: str

PCM16_MAX_ABS_VALUE: Incomplete

class LiveKitRealtimeOrchestrator:
    """[BETA] Defines the LiveKitRealtimeOrchestrator.

    This class manages the realtime conversation lifecycle.
    It handles the IO operations between the model and the input/output streamers.

    Attributes:
        room (rtc.Room): The room of the LiveKitRealtimeOrchestrator.
        task_group (asyncio.TaskGroup): The task group of the LiveKitRealtimeOrchestrator.
        input_queue (asyncio.Queue[RealtimeEvent]): The input queue of the LiveKitRealtimeOrchestrator.
        output_queue (asyncio.Queue[RealtimeEvent]): The output queue of the LiveKitRealtimeOrchestrator.
        input_streamers (list[BaseInputStreamer]): The input streamers of the LiveKitRealtimeOrchestrator.
        output_streamers (list[BaseOutputStreamer]): The output streamers of the LiveKitRealtimeOrchestrator.
        state (RealtimeState): The state of the LiveKitRealtimeOrchestrator.
    """
    room: Incomplete
    task_group: Incomplete
    input_queue: Incomplete
    output_queue: Incomplete
    input_streamers: Incomplete
    output_streamers: Incomplete
    state: Incomplete
    def __init__(self, room: rtc.Room, task_group: asyncio.TaskGroup, input_queue: asyncio.Queue[RealtimeEvent], output_queue: asyncio.Queue[RealtimeEvent], input_streamers: list[BaseInputStreamer], output_streamers: list[BaseOutputStreamer], logger: logging.Logger) -> None:
        """Initializes a new instance of the LiveKitRealtimeOrchestrator class.

        Args:
            room (rtc.Room): The room of the LiveKitRealtimeOrchestrator.
            task_group (asyncio.TaskGroup): The task group of the LiveKitRealtimeOrchestrator.
            input_queue (asyncio.Queue[RealtimeEvent]): The input queue of the LiveKitRealtimeOrchestrator.
            output_queue (asyncio.Queue[RealtimeEvent]): The output queue of the LiveKitRealtimeOrchestrator.
            input_streamers (list[BaseInputStreamer]): The input streamers of the LiveKitRealtimeOrchestrator.
            output_streamers (list[BaseOutputStreamer]): The output streamers of the LiveKitRealtimeOrchestrator.
            logger (logging.Logger): The logger of the LiveKitRealtimeOrchestrator.
        """
    async def start(self) -> None:
        """Processes the realtime conversation.

        This method is used to start the realtime conversation.
        It initializes the input and output streamers, creates the necessary tasks, and starts the conversation.
        When the conversation is terminated, it cleans up the input and output streamers.
        """

class LiveKitRealtimeSession(BaseRealtimeSession):
    '''[BETA] A realtime session module to interact with LiveKit services.

    Warning:
        The \'LiveKitRealtimeSession\' class is currently in beta and may be subject to changes in the future.
        It is intended only for quick prototyping in local environments.
        Please avoid using it in production environments.

    Attributes:
        url (str): The URL of the LiveKit server.

    Examples:
        Basic usage:
            The `LiveKitRealtimeSession` can be used as started as follows:
            ```python
            realtime_session = LiveKitRealtimeSession(url="ws://127.0.0.1:7880", token="...")
            await realtime_session.start()
            ```

        Custom IO streamers:
            The `LiveKitRealtimeSession` can be used with custom IO streamers.
            ```python
            input_streamers = [KeyboardInputStreamer(), LinuxMicInputStreamer()]
            output_streamers = [ConsoleOutputStreamer(), LinuxSpeakerOutputStreamer()]
            realtime_session = LiveKitRealtimeSession(url="ws://127.0.0.1:7880", token="...")
            await realtime_session.start(input_streamers=input_streamers, output_streamers=output_streamers)
            ```

            In the above example, we added a capability to use a Linux system microphone and speaker,
            allowing realtime audio input and output to the model.
    '''
    url: Incomplete
    api_key: Incomplete
    api_secret: Incomplete
    room_name: Incomplete
    identity: Incomplete
    def __init__(self, url: str, api_key: str | None = None, api_secret: str | None = None, room_name: str | None = None, identity: str | None = None) -> None:
        """Initializes a new instance of the LiveKitRealtimeSession class.

        Args:
            url (str): The URL of the LiveKit server.
            api_key (str | None, optional): The API key for authentication. Defaults to None,
                in which case the `LIVEKIT_API_KEY` environment variable will be used.
            api_secret (str | None, optional): The API secret for authentication. Defaults to None,
                in which case the `LIVEKIT_API_SECRET` environment variable will be used.
            room_name (str | None, optional): The name of the room. Defaults to None,
                in which case a random UUID will be used.
            identity (str | None, optional): The identity of the participant. Defaults to None,
                in which case a random UUID will be used.
        """
