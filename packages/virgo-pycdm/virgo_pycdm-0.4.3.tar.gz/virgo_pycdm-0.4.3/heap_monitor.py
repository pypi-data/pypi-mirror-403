import time
from pycdm import PyCDM
import cdm_bindings
from pycdm.structs import BsdaSettings, FramingType, EbiSettings
import zmq, json

cdm = PyCDM("127.0.0.1")
s = cdm.cdm.get_sm_state()
if s == cdm_bindings.SM_STATE.INITIALIZED:
    cdm.ebi.connect()

while True:
    i = cdm.bcg.get_info()
    if "left" in i:
        l = i["left"]["ebi"]
        uptime = l["uptime"]/1000000/60
        free = l["heap"]["largest_free_block"]
        total = l["heap"]["total_free_bytes"]
        fragmented = (total - free)/1024
        print("L UP: {:.2f}m".format(uptime))
        print("L largest_free: {:.2f}kb, total: {:.2f}kb, fragmented_waste: {:.2f}kb".format(free/1024, total/1024, fragmented))

    if "right" in i:
        r = i["right"]["ebi"]
        uptime = r["uptime"]/1000000/60
        free = r["heap"]["largest_free_block"]
        total = r["heap"]["total_free_bytes"]
        fragmented = (total - free)/1024
        print("R UP: {:.2f}m".format(uptime))
        print("R largest_free: {:.2f}kb, total: {:.2f}kb, fragmented_waste: {:.2f}kb".format(free / 1024, total / 1024, fragmented))

    time.sleep(5)

print("Closing")
cdm.close()
