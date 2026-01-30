#pragma once

// XXX: This may seem redundant but it's needed for the CDM
// to avoid including twice the same file from two different submodules
#ifndef _COMMON_CMD_
#define _COMMON_CMD_

#include <array>
#include <cstdint>

#include "adc_frames.hpp"
#include "aux.hpp"

constexpr uint8_t k_magic_byte = 0x45;

// must be increased every time that the EbiSettings, BsdaSettings, data format or any
// other struct related with how data is stored and parsed is changed
constexpr uint8_t k_abi_ver = 0x2;

// IMPORTANT: value of CONCENTRATOR, B2 and B3 must not change. They represent index in BSDA arrays.
enum class BOARD_ID : uint8_t {
    CONCENTRATOR = 0, // B1 board
    B2 = 1,
    B3 = 2,
    SERVER,
    ERBI,
    EWBI,
};

enum class BOARD_LOC : uint8_t {
    RIGHT = 0,
    LEFT = 1,
};

enum class OPERATION : uint8_t {
    GET_VERSION,
    GET_INFO,
    ECHO,
    START,
    STOP,
    CONFIGURE,
    OTA_BEGIN,
    OTA_RECV_CHUNK,
    OTA_END,
    OTA_SET_AS_BOOT,
    OTA_SET_OK,
    OTA_BACK_TO_OTA0,
    OTA_BACK_TO_FACTORY,
    RTC_SYNC,
    READ_ID,
    READ_TEMPS,
    READ_PT100,
    READ_MAC,
    INTERNAL_ECHO,
    ADC_MAP,
    ADC_FREQ,
    ADC_ONESHOT,
    RESET,
    DUMP_LOG,
    STATE,
    TIME,
    GET_PARTITION,
    CRASH_SYSTEM, // WARNING: Test function, after executing this function the system will crash
    GET_COREDUMP,
    GET_CONFIG,
    START_TEMP,
    STOP_TEMP,
    START_VOLT,
    STOP_VOLT,
    HW_TEST, // experimental
    POLLFRAMES,
    READ_VOLTAGE,
    GET_CALIB, // get voltage and temperature callibration data
    DISABLE_WIFI,

    // EBI and concentrator commands
    EBI_GET_VERSION = 0x80,
    EBI_GET_INFO,
    EBI_ECHO,
    EBI_OTA_BEGIN,
    EBI_OTA_RECV_CHUNK,
    EBI_OTA_END,
    EBI_OTA_SET_AS_BOOT,
    EBI_OTA_SET_OK,
    EBI_OTA_BACK_TO_OTA0,
    EBI_OTA_BACK_TO_FACTORY,
    EBI_RTC_SYNC,
    EBI_BUSTEST,
    EBI_RESET,
    EBI_DUMP_LOG,
    EBI_STATE,
    EBI_START_TEMP,
    EBI_STOP_TEMP,
    EBI_START_VOLT,
    EBI_STOP_VOLT,
    EBI_TIME,
    EBI_GET_PARTITION,
    EBI_GET_VOLTAGE,
    EBI_ADC_MAP,
    EBI_ADC_FREQ,
    EBI_GET_BSDA_VERSIONS,
    EBI_DISABLE_BSDA_WIFI,

    // ERBI specific commands
    EBI_CONFIGURE,
    EBI_START,
    EBI_STOP
};

enum class PACKET_TYPE : uint8_t {
    COMMAND,
    REPLY,
};

enum class FRAMING_T : uint8_t { FULL, SUM, RAW, HISTOGRAM, TEST, SUM_SQ };

enum class ASYNC_TYPE : uint8_t {
    HEARTBEAT,
    FRAME,
    TEMPS,
    VOLTAGES,
    ERROR,
};

struct __attribute__((__packed__)) AsyncHeader {
    uint8_t magic_byte;
    ASYNC_TYPE op;
    BOARD_ID board;
    FRAMING_T type;
    uint16_t count;
    uint16_t size;
};

// LOG_LEVEL_T = esp_log_level_t;    Here for use outside idf build
typedef enum {
    LOG_NONE, /*!< No log output */
    LOG_ERROR, /*!< Critical errors, software module can not recover on its own */
    LOG_WARN, /*!< Error conditions from which recovery measures have been taken */
    LOG_INFO, /*!< Information messages which describe normal flow of events */
    LOG_DEBUG, /*!< Extra information which is not necessary for normal use (values, pointers, sizes, etc). */
    LOG_VERBOSE /*!< Bigger chunks of debugging information, or frequent messages which can potentially flood the output. */
} LOG_LEVEL_T;

using AdcFreq = std::array<int, 2>;

struct __attribute__((__packed__)) BsdaSettings {
    bool disabled;

    bool light_enabled;
    bool temperature_enabled;
    bool voltage_enabled;

    // Sampling period for temperature reading
    uint16_t temperature_period_ms;
    uint16_t voltage_period_ms;

    // LightReader settings
    FRAMING_T framing;
    uint64_t frame_duration_us;
    std::array<uint16_t, 2> adc_shadow;
    AdcFreq adc_freq;
    uint8_t raw_adc, raw_channel; // for raw frame

    // Logging
    uint8_t log_uart;
    LOG_LEVEL_T log_level;
};

struct __attribute__((__packed__)) EbiSettings {
    uint32_t framereader_period; // ms
    FRAMING_T framereader_framingtype;
    BOARD_ID raw_board; // For RAW mode, select board

    BB<BsdaSettings> bsda_settings;

    uint32_t temperaturereader_period; // ms
    uint32_t voltagereader_period;

    uint16_t ntp_period; // minutes
    uint8_t log_uart;
    LOG_LEVEL_T log_level;
};

struct __attribute__((__packed__)) AdcMap {
    BOARD_ID id;
    uint8_t adc0_ce;
    uint8_t adc1_ce;
    std::array<uint8_t, k_channels_per_device> adc0;
    std::array<uint8_t, k_channels_per_device> adc1;
};

enum class STATE_EBI : uint8_t { INIT, READY, READING, DEAD, UNKNOWN };
enum class STATE_BSDA : uint8_t { INIT, READY, READING, DEAD, DISABLED };

struct BcgState {
    STATE_EBI ebi;
    BB<STATE_BSDA> bsda;
};

// It can have less than k_num_boards IDs
using BoardIds = std::initializer_list<BOARD_ID>;

struct BoardVersion {
    // XXX: would be better if it could be const char
    char version[10];
    char name[15];
    char git[50];
};

#endif
