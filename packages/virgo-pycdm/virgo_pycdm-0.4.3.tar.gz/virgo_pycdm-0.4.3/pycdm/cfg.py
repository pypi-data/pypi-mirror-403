import tomli
from appdirs import user_config_dir  # type: ignore[import-untyped]
from typing import Any

class Cfg:
    def __init__(self) -> None:
        appname = "cdm"
        cfg_dir = user_config_dir(appname)
        cfg_file = cfg_dir + "/frontend.toml"

        with open(cfg_file, mode="rb") as fp:
            self._cfg: dict[str, Any] = tomli.load(fp)

    def get_cdm_addr(self) -> str:
        return self._cfg["cdm"]
