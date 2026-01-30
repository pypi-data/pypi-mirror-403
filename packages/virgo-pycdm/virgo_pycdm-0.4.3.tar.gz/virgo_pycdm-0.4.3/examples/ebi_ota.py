from pycdm import PyCDM
from pycdm.structs import BsdaSettings, FramingType, EbiSettings
from time import sleep
cdm = PyCDM("127.0.0.1")
cdm.ebi.connect()
cdm.ebi.flash_ota("/tmp/erbi.bin")
cdm.ebi.boot_ota()
sleep(2)
cdm.ebi.mark_ota_as_ok()
cdm.close()
