from enum import Enum, auto
from typing import Any


class FramingType(Enum):
    FULL = 0
    SUM = auto()
    RAW = auto()
    HISTOGRAM = auto()
    TEST = auto()
    SUM_SQ = auto()


class BsdaSettings:

    def __init__(self) -> None:
        self.framing: FramingType = FramingType.SUM
        # s.bsda_settings[1].frame_duration_us = (f != FRAMING_T::HISTOGRAM ? 1000: 10000);
        self.frame_duration_us: int = 0
        self.temperature_period_ms: int = 0
        self.voltage_period_ms: int = 5000
        # default frequency is SPI_MASTER_FREQ_16M
        # Possible values are
        # SPI_MASTER_FREQ_8M      (80 * 1000 * 1000 / 10)   ///< 8MHz
        # SPI_MASTER_FREQ_9M      (80 * 1000 * 1000 / 9)    ///< 8.89MHz
        # SPI_MASTER_FREQ_10M     (80 * 1000 * 1000 / 8)    ///< 10MHz
        # SPI_MASTER_FREQ_11M     (80 * 1000 * 1000 / 7)    ///< 11.43MHz
        # SPI_MASTER_FREQ_13M     (80 * 1000 * 1000 / 6)    ///< 13.33MHz
        # SPI_MASTER_FREQ_16M     (80 * 1000 * 1000 / 5)    ///< 16MHz
        # SPI_MASTER_FREQ_20M     (80 * 1000 * 1000 / 4)    ///< 20MHz
        # SPI_MASTER_FREQ_26M     (80 * 1000 * 1000 / 3)    ///< 26.67MHz
        # SPI_MASTER_FREQ_40M     (80 * 1000 * 1000 / 2)    ///< 40MHz
        # SPI_MASTER_FREQ_80M     (80 * 1000 * 1000 / 1)    ///< 80MHz
        self.adc_freq_khz: list[int] = [16000, 16000]
        self.adc_shadow: list[int] = [0x03ff, 0x03ff]
        self.raw_adc: int = 0
        self.raw_channel: int = 0
        self.log_uart: bool = False
        self.log_level: int = 0
        self.disabled: bool = False
        self.light_enabled: bool = False
        self.temperature_enabled: bool = False
        self.voltage_enabled: bool = False

    def to_json(self) -> dict[str, Any]:
        if self.temperature_period_ms > (2**16)-1:
            raise ValueError("Temperature period is greater than 2**16 - 1")

        d: dict[str, Any] = {}
        d["framing"] = self.framing.value
        d["frame_duration_us"] = self.frame_duration_us
        d["temperature_period"] = self.temperature_period_ms
        d["voltage_period"] = self.voltage_period_ms
        d["adc_freq"] = self.adc_freq_khz
        d["adc_shadow"] = self.adc_shadow
        d["raw_adc"] = self.raw_adc
        d["raw_channel"] = self.raw_channel
        d["log_uart"] = self.log_uart
        d["log_level"] = self.log_level
        d["disabled"] = self.disabled
        d["light_enabled"] = self.light_enabled
        d["temperature_enabled"] = self.temperature_enabled
        d["voltage_enabled"] = self.voltage_enabled
        return d

    def from_json(self, j: dict[str, Any]) -> "BsdaSettings":
        self.framing = FramingType(j["framing"])
        self.frame_duration_us = j["frame_duration_us"]
        self.temperature_period_ms = j["temperature_period"]
        self.voltage_period_ms = j["voltage_period"]
        self.adc_freq_khz = j["adc_freq"]
        self.adc_shadow = j["adc_shadow"]
        self.raw_adc = j["raw_adc"]
        self.raw_channel = j["raw_channel"]
        self.log_uart = j["log_uart"]
        self.log_level = j["log_level"]
        self.disabled = j["disabled"]
        self.light_enabled = j["light_enabled"]
        self.temperature_enabled = j["temperature_enabled"]
        self.voltage_enabled = j["voltage_enabled"]

        return self

class EbiSettings:

    def __init__(self) -> None:
        #s.framereader_period = (f != FRAMING_T::HISTOGRAM ? 10: 100);
        self.voltage_reader_period_ms: int = 5000
        self.temperature_reader_period_ms: int = 0
        self.frame_reader_period_ms: int = 0
        self.frame_reader_framing_type: FramingType = FramingType.SUM
        self.raw_board: int = 0
        self.bsda_settings: list[BsdaSettings] = [BsdaSettings(), BsdaSettings(), BsdaSettings()]
        self.ntp_period_m: int = 0
        self.log_uart: bool = False
        self.log_level: int = 0

    def to_json(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d["voltage_reader_period"] = self.voltage_reader_period_ms
        d["temperature_reader_period"] = self.temperature_reader_period_ms
        d["period"] = self.frame_reader_period_ms
        d["type"] = self.frame_reader_framing_type.value
        d["bsda_settings"] = [s.to_json() for s in self.bsda_settings]
        d["raw_board"] = self.raw_board
        d["ntp_period_m"] = self.ntp_period_m
        d["log_level"] = self.log_level
        d["log_uart"] = self.log_uart
        return d

    def from_json(self, j: dict[str, Any]) -> "EbiSettings":
        self.voltage_reader_period_ms = j["voltage_reader_period"]
        self.temperature_reader_period_ms = j["temperature_reader_period"]
        self.frame_reader_period_ms = j["period"]
        self.frame_reader_framing_type = FramingType(j["type"])
        self.bsda_settings = [BsdaSettings().from_json(e) for e in j["bsda_settings"]]
        self.raw_board = j["raw_board"]
        self.ntp_period_m = j["ntp_period_m"]
        self.log_level = j["log_level"]
        self.log_uart = j["log_uart"]

        return self
