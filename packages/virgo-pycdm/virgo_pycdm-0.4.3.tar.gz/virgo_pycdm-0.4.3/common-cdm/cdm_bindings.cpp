#include <sstream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "common/adc_frames.hpp"
#include "common/cmd.hpp"

#include "frame_decoding.hpp"
#include "sm_defs.hpp"
#include "zmq_defs.hpp"

#define ADD_CMD(X) m.attr(#X) = CDM::CMD::X
#define ADD_SM_STATE_VAL(X) .value(#X, SM_STATE::X)
#define ADD_READWRITE(C, X) .def_readwrite(#X, &C::X)

PYBIND11_MODULE(cdm_bindings, m) {
    ADD_CMD(start);
    ADD_CMD(stop);
    ADD_CMD(ebi_echo);
    ADD_CMD(cdm_version);
    ADD_CMD(bsda_echo);
    ADD_CMD(connect);
    ADD_CMD(disconnect);
    ADD_CMD(configure);
    ADD_CMD(get_config);
    ADD_CMD(check);
    ADD_CMD(get_state);
    ADD_CMD(download_file);
    ADD_CMD(get_cdm_config);
    ADD_CMD(get_cdm_state);
    ADD_CMD(hard_reset);
    ADD_CMD(flash_bsda_ota);
    ADD_CMD(prepare_bsda_ota);
    ADD_CMD(boot_bsda_ota);
    ADD_CMD(mark_bsda_ota_ok);
    ADD_CMD(switch_bsda_factory);
    ADD_CMD(switch_bsda_ota);
    ADD_CMD(flash_ebi_ota);
    ADD_CMD(boot_ebi_ota);
    ADD_CMD(mark_ebi_ota_ok);
    ADD_CMD(switch_ebi_ota);
    ADD_CMD(switch_ebi_factory);
    ADD_CMD(dump_log);
    ADD_CMD(get_partition);
    ADD_CMD(crash);
    ADD_CMD(get_coredump);
    ADD_CMD(power_on);
    ADD_CMD(power_off);
    ADD_CMD(read_pt100);
    ADD_CMD(get_info);
    ADD_CMD(get_voltage);
    ADD_CMD(get_adc_map);
    ADD_CMD(get_adc_freq);
    ADD_CMD(get_version);
    ADD_CMD(get_warnings);
    ADD_CMD(adc_oneshot);

    pybind11::enum_<SM_STATE>(m, "SM_STATE")
        ADD_SM_STATE_VAL(INITIALIZED)
        ADD_SM_STATE_VAL(OTA_FLASH)
        ADD_SM_STATE_VAL(OTA_TEST)
        ADD_SM_STATE_VAL(ERBI_READY)
        ADD_SM_STATE_VAL(BSDA_READY)
        ADD_SM_STATE_VAL(ACQ)
        ADD_SM_STATE_VAL(ERROR)
        .export_values();

    pybind11::enum_<FRAMING_T>(m, "FramingType")
        .value("Full", FRAMING_T::FULL)
        .value("Sum", FRAMING_T::SUM)
        .value("Raw", FRAMING_T::RAW)
        .value("Histogram", FRAMING_T::HISTOGRAM)
        .value("Test", FRAMING_T::TEST)
        .value("SumSq", FRAMING_T::SUM_SQ)
        .export_values();

    pybind11::enum_<BOARD_ID>(m, "BoardId")
        .value("Concentrator", BOARD_ID::CONCENTRATOR)
        .value("B2", BOARD_ID::B2)
        .value("B3", BOARD_ID::B3)
        .value("Server", BOARD_ID::SERVER)
        .value("ERBI", BOARD_ID::ERBI)
        .value("EWBI", BOARD_ID::EWBI)
        .export_values();

    pybind11::enum_<LOG_LEVEL_T>(m, "LogLevel")
        .value("None", LOG_LEVEL_T::LOG_NONE)
        .value("Error", LOG_LEVEL_T::LOG_ERROR)
        .value("Warn", LOG_LEVEL_T::LOG_WARN)
        .value("Info", LOG_LEVEL_T::LOG_INFO)
        .value("Debug", LOG_LEVEL_T::LOG_DEBUG)
        .value("Verbose", LOG_LEVEL_T::LOG_VERBOSE)
        .export_values();

    pybind11::enum_<ASYNC_TYPE>(m, "AsyncType")
        .value("Heartbeat", ASYNC_TYPE::HEARTBEAT)
        .value("Frame", ASYNC_TYPE::FRAME)
        .value("Temps", ASYNC_TYPE::TEMPS)
        .value("Voltages", ASYNC_TYPE::VOLTAGES)
        .value("Error", ASYNC_TYPE::ERROR)
        .export_values();

    pybind11::class_<AdcMap>(m, "AdcMap")
        .def(pybind11::init<>())
        ADD_READWRITE(AdcMap, id)
        ADD_READWRITE(AdcMap, adc0_ce)
        ADD_READWRITE(AdcMap, adc1_ce)
        ADD_READWRITE(AdcMap, adc0)
        ADD_READWRITE(AdcMap, adc1);

    pybind11::class_<BsdaSettings>(m, "BsdaSettings")
        .def(pybind11::init<>())
        ADD_READWRITE(BsdaSettings, disabled)
        ADD_READWRITE(BsdaSettings, light_enabled)
        ADD_READWRITE(BsdaSettings, temperature_enabled)
        ADD_READWRITE(BsdaSettings, temperature_period_ms)
        ADD_READWRITE(BsdaSettings, voltage_enabled)
        ADD_READWRITE(BsdaSettings, voltage_period_ms)
        ADD_READWRITE(BsdaSettings, framing)
        ADD_READWRITE(BsdaSettings, frame_duration_us)
        ADD_READWRITE(BsdaSettings, adc_shadow)
        ADD_READWRITE(BsdaSettings, raw_adc)
        ADD_READWRITE(BsdaSettings, raw_channel)
        ADD_READWRITE(BsdaSettings, log_uart)
        ADD_READWRITE(BsdaSettings, log_level);

    pybind11::class_<AsyncHeader>(m, "AsyncHeader")
        .def(pybind11::init<>())
        ADD_READWRITE(AsyncHeader, magic_byte)
        ADD_READWRITE(AsyncHeader, op)
        ADD_READWRITE(AsyncHeader, board)
        ADD_READWRITE(AsyncHeader, type)
        ADD_READWRITE(AsyncHeader, count)
        ADD_READWRITE(AsyncHeader, size);

    pybind11::class_<EbiSettings>(m, "EbiSettings")
        .def(pybind11::init<>())
        .def_readwrite("framereader_period", &EbiSettings::framereader_period)
        .def_readwrite("framingtype", &EbiSettings::framereader_framingtype)
        ADD_READWRITE(EbiSettings, raw_board)
        ADD_READWRITE(EbiSettings, bsda_settings)
        ADD_READWRITE(EbiSettings, log_uart)
        ADD_READWRITE(EbiSettings, log_level);

    pybind11::class_<full_frame_channel_t>(m, "FullFrameChannel")
        ADD_READWRITE(full_frame_channel_t, sum)
        ADD_READWRITE(full_frame_channel_t, min)
        ADD_READWRITE(full_frame_channel_t, max);

    pybind11::class_<full_frame_t>(m, "FullFrame")
        ADD_READWRITE(full_frame_t, timestamp)
        ADD_READWRITE(full_frame_t, count)
        ADD_READWRITE(full_frame_t, data);

    pybind11::class_<sum_frame_channel_t>(m, "SumFrameChannel")
        ADD_READWRITE(sum_frame_channel_t, sum);

    pybind11::class_<sum_frame_t>(m, "SumFrame")
        ADD_READWRITE(sum_frame_t, timestamp)
        ADD_READWRITE(sum_frame_t, count)
        ADD_READWRITE(sum_frame_t, data);

    pybind11::class_<raw_frame_data_t>(m, "RawFrameChannel")
        ADD_READWRITE(raw_frame_data_t, value);

    pybind11::class_<raw_frame_t>(m, "RawFrame")
        ADD_READWRITE(raw_frame_t, timestamp)
        ADD_READWRITE(raw_frame_t, data);

    pybind11::class_<histogram_frame_channel_t>(m, "HistogramFrameChannel")
        ADD_READWRITE(histogram_frame_channel_t, bins);

    pybind11::class_<histogram_frame_t>(m, "HistogramFrame")
        ADD_READWRITE(histogram_frame_t, timestamp)
        ADD_READWRITE(histogram_frame_t, data);

    pybind11::class_<sum_sq_frame_channel_t>(m, "SumSqFrameChannel")
        ADD_READWRITE(sum_sq_frame_channel_t, sum)
        ADD_READWRITE(sum_sq_frame_channel_t, sum_sq);

    pybind11::class_<sum_sq_frame_t>(m, "SumSqFrame")
        ADD_READWRITE(sum_sq_frame_t, timestamp)
        ADD_READWRITE(sum_sq_frame_t, count)
        ADD_READWRITE(sum_sq_frame_t, data);

    pybind11::class_<FrameDecoder>(m, "FrameDecoder")
        .def(pybind11::init<std::string>())
        .def("get_header", &FrameDecoder::getHeader)
        .def("read_full_frame", &FrameDecoder::readFrame<full_frame_t>)
        .def("read_sum_frame", &FrameDecoder::readFrame<sum_frame_t>)
        .def("read_raw_frame", &FrameDecoder::readFrame<raw_frame_t>)
        .def("read_histogram_frame", &FrameDecoder::readFrame<histogram_frame_t>)
        .def("read_sumsq_frame", &FrameDecoder::readFrame<sum_sq_frame_t>)
        ;

    pybind11::class_<FileDecoder>(m, "FileDecoder")
        .def(pybind11::init<std::string>())
        .def("get_baffle_settings", &FileDecoder::getBaffleSettings)
        .def("get_header", &FileDecoder::getHeader)
        .def("read_full_frame", &FileDecoder::readFrame<full_frame_t>)
        .def("read_sum_frame", &FileDecoder::readFrame<sum_frame_t>)
        .def("read_raw_frame", &FileDecoder::readFrame<raw_frame_t>)
        .def("read_histogram_frame", &FileDecoder::readFrame<histogram_frame_t>)
        .def("read_sumsq_frame", &FileDecoder::readFrame<sum_sq_frame_t>)
        ;
}
