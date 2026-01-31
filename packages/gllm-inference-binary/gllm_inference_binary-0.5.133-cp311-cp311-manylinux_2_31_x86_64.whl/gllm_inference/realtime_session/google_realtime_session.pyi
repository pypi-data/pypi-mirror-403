import asyncio
import logging
from _typeshed import Incomplete
from gllm_core.schema import Tool
from gllm_inference.constants import GOOGLE_SCOPES as GOOGLE_SCOPES
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from gllm_inference.realtime_session.realtime_session import BaseRealtimeSession as BaseRealtimeSession
from gllm_inference.realtime_session.schema import RealtimeActivityType as RealtimeActivityType, RealtimeDataType as RealtimeDataType, RealtimeEvent as RealtimeEvent, RealtimeEventType as RealtimeEventType, RealtimeState as RealtimeState
from gllm_inference.schema import ToolCall as ToolCall
from google.genai.live import AsyncSession
from typing import Any

class Key:
    """Defines valid keys in Google Realtime Session."""
    ERROR: str
    OUTPUT: str
    RESULT: str

DEFAULT_LIVE_CONNECT_CONFIG: Incomplete

class GoogleRealtimeOrchestrator:
    """[BETA] Defines the GoogleRealtimeOrchestrator.

    This class manages the realtime conversation lifecycle.
    It handles the IO operations between the model and the input/output streamers.

    Attributes:
        session (AsyncSession): The session of the GoogleRealtimeOrchestrator.
        task_group (asyncio.TaskGroup): The task group of the GoogleRealtimeOrchestrator.
        input_queue (asyncio.Queue): The input queue of the GoogleRealtimeOrchestrator.
        output_queue (asyncio.Queue): The output queue of the GoogleRealtimeOrchestrator.
        input_streamers (list[BaseInputStreamer]): The input streamers of the GoogleRealtimeOrchestrator.
        output_streamers (list[BaseOutputStreamer]): The output streamers of the GoogleRealtimeOrchestrator.
        tool_dict (dict[str, Tool]): The dictionary of tools of the GoogleRealtimeOrchestrator.
        tool_call_queue (asyncio.Queue): The tool call queue of the GoogleRealtimeOrchestrator.
        state (RealtimeState): The state of the GoogleRealtimeOrchestrator.
    """
    session: AsyncSession
    task_group: Incomplete
    input_queue: Incomplete
    output_queue: Incomplete
    input_streamers: Incomplete
    output_streamers: Incomplete
    tool_dict: Incomplete
    tool_call_queue: Incomplete
    state: Incomplete
    def __init__(self, session: AsyncSession, task_group: asyncio.TaskGroup, input_queue: asyncio.Queue[RealtimeEvent], output_queue: asyncio.Queue[RealtimeEvent], input_streamers: list[BaseInputStreamer], output_streamers: list[BaseOutputStreamer], tool_dict: dict[str, Tool], logger: logging.Logger) -> None:
        """Initializes a new instance of the GoogleRealtimeOrchestrator class.

        Args:
            session (AsyncSession): The session of the GoogleRealtimeOrchestrator.
            task_group (asyncio.TaskGroup): The task group of the GoogleRealtimeOrchestrator.
            input_queue (asyncio.Queue[RealtimeEvent]): The input queue of the GoogleRealtimeOrchestrator.
            output_queue (asyncio.Queue[RealtimeEvent]): The output queue of the GoogleRealtimeOrchestrator.
            input_streamers (list[BaseInputStreamer]): The input streamers of the GoogleRealtimeOrchestrator.
            output_streamers (list[BaseOutputStreamer]): The output streamers of the GoogleRealtimeOrchestrator.
            tool_dict (dict[str, Tool]): A dictionary of tools provided to the model.
            logger (logging.Logger): The logger of the GoogleRealtimeOrchestrator.
        """
    async def start(self) -> None:
        """Processes the realtime conversation.

        This method is used to start the realtime conversation.
        It initializes the input and output streamers, creates the necessary tasks, and starts the conversation.
        When the conversation is terminated, it cleans up the input and output streamers.
        """

class GoogleRealtimeSession(BaseRealtimeSession):
    '''[BETA] A realtime session module to interact with Gemini Live models.

    Warning:
        The \'GoogleRealtimeSession\' class is currently in beta and may be subject to changes in the future.
        It is intended only for quick prototyping in local environments.
        Please avoid using it in production environments.

    Attributes:
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The Google client instance init parameters.
        config (LiveConnectConfig): The configuration for the realtime session.
        tool_dict (dict[str, Tool]): A dictionary of tools provided to the model.

    Authentication:
        The `GoogleRealtimeSession` can use either Google Gen AI or Google Vertex AI.

        Google Gen AI is recommended for quick prototyping and development.
        It requires a Gemini API key for authentication.

        Usage example:
        ```python
        realtime_session = GoogleRealtimeSession(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025",
            api_key="your_api_key"
        )
        ```

        Google Vertex AI is recommended to build production-ready applications.
        It requires a service account JSON file for authentication.

        Usage example:
        ```python
        realtime_session = GoogleRealtimeSession(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025",
            credentials_path="path/to/service_account.json"
        )
        ```

        If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
        The `GOOGLE_API_KEY` environment variable will be used for authentication.

    Examples:
        Basic usage:
            The `GoogleRealtimeSession` can be used as started as follows:
            ```python
            realtime_session = GoogleRealtimeSession(model_name="gemini-live-2.5-flash-preview")
            await realtime_session.invoke()
            ```

        Tool calling:
            The `GoogleRealtimeSession` can call provided tools to perform certain tasks.
            This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

            Usage example:
            ```python
            tools = [get_weather, get_temperature]
            realtime_session = GoogleRealtimeSession(model_name="gemini-live-2.5-flash-preview", tools=tools)
            await realtime_session.start()
            ```

        Custom IO streamers:
            The `GoogleRealtimeSession` can be used with custom IO streamers.
            ```python
            input_streamers = [KeyboardInputStreamer(), LinuxMicInputStreamer()]
            output_streamers = [ConsoleOutputStreamer(), LinuxSpeakerOutputStreamer()]
            realtime_session = GoogleRealtimeSession(model_name="gemini-live-2.5-flash-preview")
            await realtime_session.start(input_streamers=input_streamers, output_streamers=output_streamers)
            ```

            In the above example, we added a capability to use a Linux system microphone and speaker,
            allowing realtime audio input and output to the model.
    '''
    model_name: Incomplete
    client_params: Incomplete
    config: Incomplete
    tool_dict: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, credentials_path: str | None = None, project_id: str | None = None, location: str = 'us-central1', tools: list[Tool] | None = None, config: dict[str, Any] | None = None) -> None:
        '''Initializes a new instance of the GoogleRealtimeChat class.

        Args:
            model_name (str): The name of the model to use.
            api_key (str | None, optional): Required for Google Gen AI authentication. Cannot be used together
                with `credentials_path`. Defaults to None.
            credentials_path (str | None, optional): Required for Google Vertex AI authentication. Path to the service
                account credentials JSON file. Cannot be used together with `api_key`. Defaults to None.
            project_id (str | None, optional): The Google Cloud project ID for Vertex AI. Only used when authenticating
                with `credentials_path`. Defaults to None, in which case it will be loaded from the credentials file.
            location (str, optional): The location of the Google Cloud project for Vertex AI. Only used when
                authenticating with `credentials_path`. Defaults to "us-central1".
            tools (list[Tool] | None, optional): Tools provided to the model to enable tool calling. Defaults to None.
            config (dict[str, Any] | None, optional): Additional configuration for the realtime session.
                Defaults to None.

        Note:
            If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
            The `GOOGLE_API_KEY` environment variable will be used for authentication.
        '''
