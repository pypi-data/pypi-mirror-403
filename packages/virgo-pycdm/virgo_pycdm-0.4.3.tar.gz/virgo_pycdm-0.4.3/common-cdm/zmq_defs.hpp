#include <string_view>

namespace CDM {

namespace CMD {
constexpr std::string_view start = "start_acq";
constexpr std::string_view stop = "stop_acq";
constexpr std::string_view ebi_echo = "ebi_echo";
constexpr std::string_view cdm_version = "cdm_version";
constexpr std::string_view bsda_echo = "bsda_echo";
constexpr std::string_view connect = "connect";
constexpr std::string_view disconnect = "disconnect";
constexpr std::string_view configure = "configure_baffle";
constexpr std::string_view get_config = "get_baffle_config";
constexpr std::string_view check = "check_comm";
constexpr std::string_view get_state = "get_state";
constexpr std::string_view download_file = "download_file";
constexpr std::string_view get_cdm_config = "get_cdm_config";
constexpr std::string_view get_cdm_state = "get_cdm_state";
constexpr std::string_view hard_reset = "hard_reset";
constexpr std::string_view dump_log = "dump_log";
constexpr std::string_view flash_bsda_ota = "flash_ota";
constexpr std::string_view prepare_bsda_ota = "prepare_ota";
constexpr std::string_view boot_bsda_ota = "boot_ota";
constexpr std::string_view mark_bsda_ota_ok = "mark_ota_as_ok";
constexpr std::string_view switch_bsda_ota = "switch_bsda_to_ota";
constexpr std::string_view switch_bsda_factory = "switch_bsda_to_factory";
constexpr std::string_view flash_ebi_ota = "flash_ebi_ota";
constexpr std::string_view boot_ebi_ota = "boot_ebi_ota";
constexpr std::string_view mark_ebi_ota_ok = "mark_ebi_ota_as_ok";
constexpr std::string_view switch_ebi_ota = "switch_ebi_to_ota";
constexpr std::string_view switch_ebi_factory = "switch_ebi_to_factory";
constexpr std::string_view get_partition = "get_partition_labels";
constexpr std::string_view crash = "crash_system";
constexpr std::string_view get_coredump = "get_coredump";
constexpr std::string_view power_on = "power_on";
constexpr std::string_view power_off = "power_off";
constexpr std::string_view read_pt100 = "read_pt100";
constexpr std::string_view get_info = "get_info";
constexpr std::string_view get_voltage = "get_voltage";
constexpr std::string_view get_adc_map = "get_adc_map";
constexpr std::string_view get_adc_freq = "get_adc_freq";
constexpr std::string_view get_version = "get_version";
constexpr std::string_view get_warnings = "get_warns";
constexpr std::string_view adc_oneshot = "adc_oneshot";
} // namespace CMD

} // namespace CDM

namespace MSG_ID {

constexpr auto PsVoltage = "PS.VLT";
constexpr auto PsCurrent = "PS.AMP";
constexpr auto LastComm = "LAST_COMM";
constexpr auto Disk = "DISK";
constexpr auto System = "SYSTEM";
constexpr auto SystemState = "SYSTEM_STATE";
constexpr std::string_view Frame = "DATA.FRAME";
constexpr std::string_view Temp = "DATA.TEMP";
constexpr std::string_view FilteredTemp = "DATA.FILTERED_TEMP";
constexpr std::string_view BoardVoltage = "DATA.VLT";

} // namespace MSG_ID
