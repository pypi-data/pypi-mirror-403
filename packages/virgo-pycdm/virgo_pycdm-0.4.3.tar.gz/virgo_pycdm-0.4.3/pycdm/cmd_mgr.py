import json
from typing import Any

import cdm_bindings

from .comm import ZmqSyncConn
from .structs import EbiSettings
from .utils import *

"""
for the list of implemented commands see cmd.cpp:CmdExecutor::execute
"""
class CmdUtils:
    def __init__(self, addr: str) -> None:
        self._cdm_cmd: ZmqSyncConn = ZmqSyncConn(addr)

    def flash(self, fname: str, cmd: str) -> dict[str, Any]:
        fw, h = encode_from_file(fname)
        args = {"hash": h, "firmware_data": fw.decode()}
        return self.process(cmd, args)

    def process(self, cmd: str, args: dict[str, Any] = {}) -> dict[str, Any]:
        msg = json.dumps({"cmd": cmd, "args": args})
        self._cdm_cmd.send(msg)

        ans = json.loads(self._cdm_cmd.recv())
        if ans is None:
            return {}

        err = ans.pop("error", None)
        if err is not None:
            raise Exception(err)

        return ans

    def download(self, cmd: str, dst: str, key: str, args: dict[str, Any] = {}) -> dict[str, Any]:
        ans = self.process(cmd, args)
        decode_to_file(ans[key], dst)
        del ans[key]
        return ans


class CdmCmd:
    def __init__(self, cmd: CmdUtils) -> None:
        self._cmd: CmdUtils = cmd

    def get_info(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.cdm_version)

    def get_sm_state(self) -> Any:
        return cdm_bindings.SM_STATE(self._cmd.process(cdm_bindings.get_cdm_state)["state"])

    def get_config(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_cdm_config)

    def download_file(self, year: int, month: int, day: int, hour: int, fname: str, dpath: str) -> dict[str, Any]:
        d = {"year": year, "month": month, "day": day, "hour": hour, "file_name": fname}
        return self._cmd.download(cdm_bindings.download_file, dpath, "file_content", d)

    def power_on(self, s: str = "") -> dict[str, Any]:
        if s != "I_KNOW_WHAT_I_AM_DOING":
            raise Exception("Not allowed to use this method")

        return self._cmd.process(cdm_bindings.power_on, {"is_engineer": True})

    def power_off(self, s: str = "") -> dict[str, Any]:
        if s != "I_KNOW_WHAT_I_AM_DOING":
            raise Exception("Not allowed to use this method")

        return self._cmd.process(cdm_bindings.power_off, {"is_engineer": True})

    def get_warnings(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_warnings)


"""
Bcg stands for "Baffle control group". A BCG is the combination of 1 ERBI plus 3 BSDAs.
There are two BCG each one controlled by one ERBI (or a concentrator BSDA).
"""

class BcgCmd:
    def __init__(self, cmd: CmdUtils) -> None:
        self._cmd: CmdUtils = cmd

    def get_running_partition(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_partition)

    def get_info(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_info)

    def get_voltage(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_voltage)

    def get_adc_map(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_adc_map)

    def get_adc_freq(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_adc_freq)

    def adc_oneshot(self, b: str, adc: int, ch: int) -> Any:
        args = {"board_identifier": b, "adc": adc, "ch": ch}
        return self._cmd.process(cdm_bindings.adc_oneshot, args)["val"]

    def get_config(self) -> tuple[EbiSettings, EbiSettings]:
        s = self._cmd.process(cdm_bindings.get_config)
        left = EbiSettings().from_json(s["left"])
        right = EbiSettings().from_json(s["right"])
        return left, right

    def get_state(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_state)

    def dump_log(self, idns: list[str]) -> dict[str, list[str]]:
        """
        :param idns: List of valid identifiers. Can be any of {R,L} or {R,L}{0,1,2}
        """
        for i in idns:
            check_valid_board_identifier(i)

        args = {"board_identifiers": idns}
        ans = self._cmd.process(cdm_bindings.dump_log, args)

        for k, v in ans.items():
            ans[k] = v.splitlines()

        return ans

    def hard_reset(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.hard_reset, {"reset_erbi": True, "reset_bsdas": True})

    def versions(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.get_version)


class EbisCmd:
    def __init__(self, cmd: CmdUtils) -> None:
        self._cmd: CmdUtils = cmd

    # XXX: Maybe this function should be moved to CDM class as it's the CDM who is connecting to the EBI
    # the EBI is not connecting anywhere
    def connect(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.connect)

    def disconnect(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.disconnect)

    def echo(self, ebi: str) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.ebi_echo, {"ebi": ebi})

    def flash_ota(self, fname: str) -> dict[str, Any]:
        return self._cmd.flash(fname, cdm_bindings.flash_ebi_ota)

    def boot_ota(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.boot_ebi_ota)

    def mark_ota_as_ok(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.mark_ebi_ota_ok)

    def switch_to_factory(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.switch_ebi_factory)

    def switch_to_ota(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.switch_ebi_ota)

    def hard_reset(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.hard_reset, {"reset_erbi": True, "reset_bsdas": False})


class BsdasCmd:
    def __init__(self, cmd: CmdUtils) -> None:
        self._cmd: CmdUtils = cmd

    def echo(self, ebi: str, bsda: int) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.bsda_echo, {"ebi": ebi, "bsda": bsda})

    def boot_ota(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.boot_bsda_ota)

    def crash_system(self, idn: str) -> dict[str, Any]:
        """
        :param idn: A board identifier, it must be one of {R,L}{0,1,2}
        """
        check_valid_board_identifier(idn)
        return self._cmd.process(cdm_bindings.crash, {"board_identifier": idn})

    def get_coredump(self, idn: str, dpath: str) -> dict[str, Any]:
        """
        :param idn: A board identifier, it must be one of {R,L}{0,1,2}
        :param out_path: File where coredump will be saved
        """
        idn = check_valid_board_identifier(idn)
        # check that a BSDA is select and not only one of the ERBIs
        if len(idn) != 2:
            raise Exception("Invalid board identifier")

        return self._cmd.download(cdm_bindings.get_coredump, dpath, "coredump", {"board_identifier": idn})

    def prepare_ota(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.prepare_bsda_ota)

    def flash_ota(self, fname: str) -> dict[str, Any]:
        return self._cmd.flash(fname, cdm_bindings.flash_bsda_ota)

    def mark_ota_as_ok(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.mark_bsda_ota_ok)

    def switch_to_ota(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.switch_bsda_ota)

    def switch_to_factory(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.switch_bsda_factory)

    def hard_reset(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.hard_reset, {"reset_erbi": False, "reset_bsdas": True})
