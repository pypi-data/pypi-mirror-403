import pytest
from time import sleep

from pycdm import PyCDM
from pycdm.structs import BsdaSettings, FramingType, EbiSettings
import cdm_bindings

"""
XXX: this integration tests only works with a single BCG, not an entire baffle. If both halves are present, the test is not valid.
"""

def test_cfg():
    s = PyCDM("127.0.0.1")
    s._cfg.get_cdm_addr()
    s.close()

def test_cdm_commands(tmpdir):
    s = PyCDM("127.0.0.1")
    s.cdm.get_info()
    s.cdm.get_config()
    s.cdm.get_warnings()
    assert s.cdm.get_sm_state() == cdm_bindings.SM_STATE.INITIALIZED
    s.cdm.power_off("I_KNOW_WHAT_I_AM_DOING")
    s.cdm.power_on("I_KNOW_WHAT_I_AM_DOING")
    with pytest.raises(Exception):
        s.cdm.power_off()
    with pytest.raises(Exception):
        s.cdm.power_on()
    s.cdm.download_file(2025, 4, 1, 12, "PS.VLT", "{}/file".format(tmpdir)) # XXX fix the hardocded file name or ensure to create it
    s.close()

def test_ebi_commands():
    s = PyCDM("127.0.0.1")
    s.ebi.connect()
    try:
        r = s.bcg.get_state()
        loc = "right" if r["right"] else "left"
        s.ebi.echo(loc[0])
        prev = s.bcg.get_info()
        s.ebi.hard_reset()
        sleep(5)
        s.ebi.connect()
        aft = s.bcg.get_info()
        assert prev[loc]["ebi"]["uptime"] > aft[loc]["ebi"]["uptime"]
        for i, k  in zip(prev[loc]["bsda"], aft[loc]["bsda"]):
            # BSDA are not reset, so the uptime should have increased
            assert i["uptime"] < k["uptime"]
    finally:
        s.ebi.disconnect()
        s.close()

def test_bsda_commands(tmpdir):
    s = PyCDM("127.0.0.1")
    s.ebi.connect()
    try:
        r = s.bcg.get_state()
        loc = "right" if r["right"] else "left"
        for i in range(3):
            s.bsda.echo(loc[0], i)
        prev = s.bcg.get_info()
        s.bsda.hard_reset()
        sleep(5)
        aft = s.bcg.get_info()
        # EBI is not reset
        assert prev[loc]["ebi"]["uptime"] < aft[loc]["ebi"]["uptime"]
        for i, k  in zip(prev[loc]["bsda"], aft[loc]["bsda"]):
            assert i["uptime"] > k["uptime"]

    finally:
        s.ebi.disconnect()
        s.close()


def test_bcg_commands(tmpdir):
    s = PyCDM("127.0.0.1")
    s.ebi.connect()
    try:
        s.bcg.get_running_partition()
        s.bcg.get_voltage()
        s.bcg.get_adc_map()
        s.bcg.get_config()
        s.bcg.versions()
        r = s.bcg.get_state()
        loc = "right" if r["right"] else "left"
        prev = s.bcg.get_info()
        if loc == "right":
            s.bcg.dump_log(["R", "R0", "R1", "R2"])
        else:
            s.bcg.dump_log(["L", "L0", "L1", "L2"])

        s.bcg.hard_reset()
        sleep(5)
        s.ebi.connect()
        aft = s.bcg.get_info()
        assert prev[loc]["ebi"]["uptime"] > aft[loc]["ebi"]["uptime"]
        for i, k  in zip(prev[loc]["bsda"], aft[loc]["bsda"]):
            assert i["uptime"] > k["uptime"]
    finally:
        s.ebi.disconnect()
        s.close()

def test_short_acq(tmpdir):
    bsda = BsdaSettings()
    bsda.framing = FramingType.SUM_SQ
    bsda.frame_duration_us = 1000
    bsda.temperature_period_ms = 1000
    bsda.voltage_period_ms = 12000
    bsda.adc_shadow = [0xf9f0, 0xf9f0]
    bsda.log_uart = True
    bsda.log_level = 3
    bsda.raw_adc = 1
    bsda.raw_channel = 1
    bsda.disabled = False
    bsda.light_enabled = True
    bsda.temperature_enabled = True
    bsda.voltage_enabled = True

    bsda_disabled = BsdaSettings()
    bsda_disabled.disabled = True

    left = EbiSettings()
    left.frame_reader_framing_type = FramingType.SUM_SQ
    left.frame_reader_period_ms = 15
    left.temperature_reader_period_ms = 10000
    left.voltage_reader_period_ms = 12000
    left.raw_board = 0
    left.bsda_settings[0] = bsda
    left.bsda_settings[1] = bsda
    left.bsda_settings[2] = bsda
    left.ntp_period_m = 1
    left.log_uart = True
    left.log_level = 2

    right = EbiSettings()
    right.frame_reader_framing_type = FramingType.SUM_SQ
    right.frame_reader_period_ms = 15
    right.temperature_reader_period_ms = 10000
    right.voltage_reader_period_ms = 12000
    right.raw_board = 1
    right.bsda_settings[0] = bsda
    right.bsda_settings[1] = bsda
    right.bsda_settings[2] = bsda
    right.ntp_period_m = 1
    right.log_uart = True
    right.log_level = 2

    s = PyCDM("127.0.0.1")
    s.ebi.connect()
    try:
        r = s.bcg.get_state()
        # At least one side have to be available for the reading
        if r["right"] is None:
            right.bsda_settings[0] = bsda_disabled
            right.bsda_settings[1] = bsda_disabled
            right.bsda_settings[2] = bsda_disabled
        elif r["left"] is None:
            left.bsda_settings[0] = bsda_disabled
            left.bsda_settings[1] = bsda_disabled
            left.bsda_settings[2] = bsda_disabled

        s.configure(left, right)
        # configure two times to test the other path and also to test the re-configure
        s.configure(left)

        s.start_acq()
        # 2 minutes should be enough to exercise the voltage, ntp, temperature and light readers
        sleep(2 * 60)
        s.stop_acq()
    finally:
        s.ebi.disconnect()
        s.close()
