from gllm_inference.realtime_session.schema.realtime_event import RealtimeEventType as RealtimeEventType
from pydantic import BaseModel

class RealtimeState(BaseModel):
    """[BETA] Defines the realtime state of the realtime session module with thread-safe properties.

    Attributes:
        interruption (bool): Whether an interruption is active, causing non-activity events to be filtered.
        console_mode (RealtimeEventType): The currently active console mode.
    """
    interruption: bool
    console_mode: RealtimeEventType
    async def set_interruption(self, value: bool) -> None:
        """Thread-safe setter for interruption.

        Args:
            value (bool): The value to set for interruption.
        """
    async def get_interruption(self) -> bool:
        """Thread-safe getter for interruption.

        Returns:
            bool: The value of interruption.
        """
    async def set_console_mode(self, value: RealtimeEventType) -> None:
        """Thread-safe setter for console_mode.

        Args:
            value (RealtimeEventType): The value to set for console_mode.
        """
    async def get_console_mode(self) -> RealtimeEventType:
        """Thread-safe getter for console_mode.

        Returns:
            RealtimeEventType: The value of console_mode.
        """
    def set_terminated(self) -> None:
        """Set termination state.

        Sets the termination event. This is thread-safe as asyncio.Event operations are inherently thread-safe.
        """
    def get_terminated(self) -> bool:
        """Get termination state.

        Returns:
            bool: True if terminated, False otherwise.
        """
    async def wait_terminated(self) -> None:
        """Wait for termination to be signaled.

        This method blocks until termination is set to True, providing instant notification.
        """
