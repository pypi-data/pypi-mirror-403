class InputAudioConfig:
    """Defines constants for input audio processing.

    Notes:
        16 kHz is used as it is commonly used for speech input and is sufficient
        to capture the full frequency range of human speech while keeping latency
        and bandwidth low.
    """
    SAMPLE_RATE: int
    CHANNELS: int
    CHUNK_DURATION: float
    BYTES_PER_SAMPLE: int

class OutputAudioConfig:
    """Defines constants for output audio processing.

    Notes:
        24 kHz is used as it is commonly used for speech synthesis output to
        provide better clarity and naturalness compared to 16 kHz, while remaining
        lightweight for realtime playback.
    """
    SAMPLE_RATE: int
    CHANNELS: int
    DELAY: float

class NoiseThreshold:
    """Defines constants for noise threshold."""
    RMS: float
    SPIKE: float
    SPIKE_RATIO: float
