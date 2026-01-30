import signal
from types import FrameType
from typing import Any

import cdm_bindings

from .cfg import Cfg
from .data_mgr import DataManager, MsgReg
from .cmd_mgr import CmdUtils, CdmCmd, BcgCmd, EbisCmd, BsdasCmd
from .structs import EbiSettings

class PyCDM:
    """
    This class exports only the bare minimum commands needed for the normal operation of the system.
    All other commands are exported by the different classes contained by this one.
    """
    def __init__(self, cdm_addr: str = "") -> None:
        self._cfg: Cfg = Cfg()
        if cdm_addr == "":
            cdm_addr = self._cfg.get_cdm_addr()
        self._cmd: CmdUtils = CmdUtils(cdm_addr)
        self._data: DataManager = DataManager(cdm_addr)
        signal.signal(signal.SIGINT, self._handler)

        # Commands targeted to CDM
        self.cdm: CdmCmd = CdmCmd(self._cmd)

        # Commands targeted to one or more BCG(s)
        self.bcg: BcgCmd = BcgCmd(self._cmd)

        # Commands targeted at one or more EBI(s)
        self.ebi: EbisCmd = EbisCmd(self._cmd)

        # Commands targeted at one or more BSDA(s)
        self.bsda: BsdasCmd = BsdasCmd(self._cmd)

    def _handler(self, signum: int, frame: FrameType | None) -> None:
        self.close()

    def close(self) -> None:
        self._data.close()

    def check_comm(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.check)

    def configure(self, baffle_settings: EbiSettings, right_baffle_settings: EbiSettings | None = None) -> dict[str, Any]:
        if right_baffle_settings:
            d = {"left": baffle_settings.to_json(), "right": right_baffle_settings.to_json()}
            return self._cmd.process(cdm_bindings.configure, d)
        else:
            d = {"left": baffle_settings.to_json(), "right": baffle_settings.to_json()}
            return self._cmd.process(cdm_bindings.configure, d)

    def start_acq(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.start)

    def stop_acq(self) -> dict[str, Any]:
        return self._cmd.process(cdm_bindings.stop)

    def read_pt100(self, ebi: str, bsda: int) -> tuple[list[float | int], int, float]:
        uv = self._cmd.process(cdm_bindings.read_pt100, {"ebi": ebi, "bsda": bsda})["ans"]
        uva = uv[0]
        uvb = uv[1]

        r1 = 500
        vcc = 3.37
        vdiff = abs(uva-uvb)/1000.0/1000.0

        rpt100 = (r1 * vdiff + 100 * vcc) / (vcc - vdiff)
        return uv, r1, (rpt100 - 100.0) / 0.39083

    def reg_msg(self, s: str) -> MsgReg:
        return self._data.register(s)
