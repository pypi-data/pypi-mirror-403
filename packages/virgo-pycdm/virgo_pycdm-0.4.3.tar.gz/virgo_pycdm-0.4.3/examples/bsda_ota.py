from time import sleep
from pycdm import PyCDM
from pycdm.structs import BsdaSettings, FramingType, EbiSettings

cdm = PyCDM()
cdm.bsda.prepare_ota()
cdm.bsda.flash_ota("/tmp/bsda.bin")
cdm.bsda.boot_ota()
sleep(2)
cdm.bsda.mark_ota_as_ok()
cdm.close()
