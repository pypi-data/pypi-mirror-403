"""Common definitions for the timing models."""

from enum import IntEnum

MIN_PLAYZERO_SAMPLES = 32
PLAYZERO_GRANULARITY = 16
SAMPLE_FREQUENCY = 2.0e9


class TriggerSource(IntEnum):
    """QCCS system trigger sources."""

    ZSYNC = 1
    INTERNAL = 2
