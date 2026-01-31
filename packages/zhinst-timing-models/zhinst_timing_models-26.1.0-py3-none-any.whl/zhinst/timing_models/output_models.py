"""Output latency models for the Zurich Instruments QCCS instruments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Union

import yaml

from zhinst.timing_models.common import (
    MIN_PLAYZERO_SAMPLES,
    PLAYZERO_GRANULARITY,
    SAMPLE_FREQUENCY,
    TriggerSource,
)


@dataclass
class PrecompensationConf:
    """HDAWG Precompensation configuration."""

    """High pass compensation enabled"""
    highpass_enable: bool = False
    """Number of exponential filters used"""
    exponentials_count: int = 0
    """Bounce compensation enabled"""
    bounces_enable: bool = False
    """FIR filter enabled"""
    fir_enable: bool = False


@dataclass
class AlignmentSettings:
    """Device settings to allow output alignment in a QCCS system."""

    """The number of samples to play zero after the trigger."""
    playzero_samples: int = 0
    """The delay in seconds to apply to the signal output in the corresponding node."""
    sigout_delay: float = 0.0


class _DeviceChannelOutputModel(ABC):
    """Base class for output latency models."""

    _TARGET_LATENCY = 900 * 2  # samples

    def __init__(self, dev_type: str) -> None:
        dir_path = Path(__file__).resolve().parent
        with (dir_path / "trigger_latencies.yml").open("r") as file:
            t2o_latencies = yaml.safe_load(file)
        self.base_latency = t2o_latencies.get(dev_type)

    @abstractmethod
    def get_sigout_delay_limit(self) -> float:
        """Return the maximum allowed signal output delay."""
        ...

    @abstractmethod
    def get_latency(self, *args, **kwargs) -> int:  # noqa: ANN002, ANN003
        """Return the output latency of the instrument for the given configuration."""
        ...

    def get_alignment_settings(
        self,
        user_delay: float = 0.0,
        *args: tuple,
        **kwargs: dict,
    ) -> AlignmentSettings:
        """Return alingment settings for the given configuration.

        Args:
            user_delay (float, optional): The desired additional user delay,
                beyond the delay required to align the channel, in seconds.
            *args: Same as the get_latency method.
            **kwargs: Same as the get_latency method.

        Returns:
            AlignmentSettings: The alignment settings.
        """
        latency_samples = self.get_latency(*args, **kwargs)
        target_latency = self._TARGET_LATENCY + ceil(
            user_delay / (1 / SAMPLE_FREQUENCY),
        )
        additional_delay_samples = target_latency - latency_samples
        playzero_samples = PLAYZERO_GRANULARITY * (
            additional_delay_samples // PLAYZERO_GRANULARITY
        )
        playzero_samples = (
            playzero_samples if playzero_samples >= MIN_PLAYZERO_SAMPLES else 0
        )

        if playzero_samples < 0:
            err = f"The desired {user_delay=} is a large negative number and forces \
                the playzero samples to be negative."
            raise ValueError(err)

        sigout_delay_seconds = (additional_delay_samples - playzero_samples) * (
            1 / SAMPLE_FREQUENCY
        )

        return AlignmentSettings(playzero_samples, sigout_delay_seconds)


class HDAWGChannelModel(_DeviceChannelOutputModel):
    """HDAWG channel output latency model."""

    _HPC_LATENCY = 96
    _EXP_LATENCY = 88
    _BSC_LATENCY = 32
    _FIR_LATENCY = 136
    _PRECOMP_LATENCY = 72
    _SIGOUT_DELAY_MAX_LIMIT = 62 / SAMPLE_FREQUENCY

    def __init__(self) -> None:
        """Initialize the HDAWG channel output latency model."""
        super().__init__("hdawg")

    def get_sigout_delay_limit(self) -> float:
        """Return the maximum allowed signal output delay."""
        return self._SIGOUT_DELAY_MAX_LIMIT

    def get_latency(
        self,
        precompensation_enabled: int = 0,
        precompensation_conf: Union[PrecompensationConf, None] = None,  # noqa: UP007
        direct_enabled: int = 0,
    ) -> int:
        """Return the output latency of the instrument for the given configuration.

        Args:
            precompensation_enabled (int, optional):
                '1' when precompensation is enabled. Defaults to '0'.
            precompensation_conf (PrecompensationConf):
                The Precompensation configuration.
            direct_enabled (int, optional):
                '1' when direct output is enabled. Defaults to '0'.

        Returns:
            int: The expected latency in samples.
        """
        latency = 0
        if precompensation_enabled:
            latency = self._PRECOMP_LATENCY
            if precompensation_conf:
                if precompensation_conf.highpass_enable:
                    latency += self._HPC_LATENCY
                if precompensation_conf.exponentials_count > 0:
                    latency += (
                        self._EXP_LATENCY * precompensation_conf.exponentials_count
                    )
                if precompensation_conf.bounces_enable:
                    latency += self._BSC_LATENCY
                if precompensation_conf.fir_enable:
                    latency += self._FIR_LATENCY
        if direct_enabled:
            latency -= 3

        # return the latency in samples
        return int(self.base_latency["zsync_trigger"] + latency)


class SGChannelModel(_DeviceChannelOutputModel):
    """SHFSG channel output latency model."""

    _MAX_ROUTER_PATHS_PER_CHANNEL = 3
    _SIGOUT_DELAY_MAX_LIMIT = 124e-9

    def __init__(self) -> None:
        """Initialize the SHFSG channel output latency model."""
        super().__init__("sg")

    def get_sigout_delay_limit(self) -> float:
        """Return the maximum allowed signal output delay."""
        return self._SIGOUT_DELAY_MAX_LIMIT

    def get_latency(
        self,
        *,
        rflfpath: str | int = "rf",
        outputrouter_enable: int = 0,
        trigger: TriggerSource = TriggerSource.ZSYNC,
    ) -> int:
        """Return the output latency of the instrument for the given configuration.

        Args:
            rflfpath (str | int, optional): Specifies the path type.
                Use "rf" for RF path or "lf" for LF path. Defaults to "rf".
                When used as int, '1' corresponds to "rf" and '0' to "lf".
            outputrouter_enable (int, optional): '1' when the
                output router is enabled. Defaults to '0'.
            trigger (TriggerSource, optional): The trigger source.
                Defaults to TriggerSource.ZSYNC.

        Raises:
            TypeError: If the trigger is not an instance of TriggerSource.
            ValueError: If rtr_c is not within the valid range.

        Returns:
            int: The calculated latency in samples.
        """
        path = ("rf" if rflfpath else "lf") if isinstance(rflfpath, int) else rflfpath

        latency = self.base_latency[trigger.name.lower() + "_trigger"][path]
        if outputrouter_enable:
            latency += 52  # 52 additional samples when the output router is used

        return latency


class QAChannelOutModel(_DeviceChannelOutputModel):
    """SHFQA channel output latency model."""

    _SIGOUT_DELAY_MAX_LIMIT = 124e-9

    def __init__(self) -> None:
        """Initialize the SHFQA channel output latency model."""
        super().__init__("qa")

    def get_sigout_delay_limit(self) -> float:
        """Return the maximum allowed signal output delay."""
        return self._SIGOUT_DELAY_MAX_LIMIT

    def get_latency(
        self,
        rflfpath: str | int = "rf",
        trigger: TriggerSource = TriggerSource.ZSYNC,
    ) -> int:
        """Return the output latency of the instrument for the given configuration.

        Args:
            rflfpath (str | int, optional): Specifies the path type.
                Use "rf" for RF path or "lf" for LF path. Defaults to "rf".
                When used as bool, '1' corresponds to "rf" and '0'' to "lf".
            trigger (TriggerSource, optional): The trigger source.
                Defaults to TriggerSource.ZSYNC.

        Raises:
            ValueError: If the trigger is not an instance of TriggerSource.

        Returns:
            int: The calculated latency in samples.
        """
        path = ("rf" if rflfpath else "lf") if isinstance(rflfpath, int) else rflfpath
        return self.base_latency[trigger.name.lower() + "_trigger"][path]


def equalize_playzero_samples(
    alignment_settings: list[AlignmentSettings],
    maximum_sigout_delay: Union[float, None] = None,  # noqa: UP007
) -> list[AlignmentSettings]:
    """Equalizes the number of playzero samples for channels that require it.

    This is needed for:
     - SG channels of the same instruments that use the output router
       and different rflfpath settings.
     - HDAWG channels that share the same sequencer and
       different 'direct_enable' setting

    Args:
        alignment_settings (list[tuple[int, int]]):
            A list of tuples containing the playzero samples and delay seconds
            for each affected channel.
        maximum_sigout_delay (float, optional): The maximum allowed value
            signal delay that is supported from the output delay node, for
            the type of instrument used. Defaults to None.

    Returns:
        list[AlignmentSettings]: The updated alignment settings in the same order.
    """
    playzero_min = min(
        alignment_settings,
        key=lambda x: x.playzero_samples,
    ).playzero_samples

    processed_alignment_settings = []
    for align in alignment_settings:
        delay = align.sigout_delay + (align.playzero_samples - playzero_min) * (
            1 / SAMPLE_FREQUENCY
        )
        if maximum_sigout_delay and delay > maximum_sigout_delay:
            err = f"The calculated output delay ({delay}) \
                exceeds the maximum limit ({maximum_sigout_delay})."
            raise ValueError(err)
        processed_alignment_settings.append(AlignmentSettings(playzero_min, delay))

    return processed_alignment_settings
