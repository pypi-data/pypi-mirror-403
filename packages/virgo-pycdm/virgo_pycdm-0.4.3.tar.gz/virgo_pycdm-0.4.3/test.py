import time
from pycdm import PyCDM
import cdm_bindings
from pycdm.structs import BsdaSettings, FramingType, EbiSettings
import zmq, json
import threading

bsda = BsdaSettings()
bsda.framing = FramingType.SUM_SQ
bsda.frame_duration_us = 1000
bsda.temperature_period_ms = 3000
bsda.voltage_period_ms = 5000
#bsda.adc_shadow = [0xf9f, 0xf9f]
bsda.adc_shadow = [0xf9f0, 0xf9f0]
bsda.log_uart = True
bsda.log_level = 2
bsda.raw_adc = 1
bsda.raw_channel = 1
bsda.disabled = False
bsda.imu_enabled = False
bsda.light_enabled = True
bsda.temperature_enabled = False
bsda.voltage_enabled = False

bsda2 = BsdaSettings()
bsda2.framing = FramingType.SUM_SQ
bsda2.frame_duration_us = 1000
bsda2.temperature_period_ms = 30000
bsda2.voltage_period_ms = 33000
#bsda2.adc_shadow = [0xf9f, 0xf9f]
bsda2.adc_shadow = [0xf9f0, 0xf9f0]
bsda2.log_uart = True
bsda2.log_level = 2
bsda2.raw_adc = 1
bsda2.raw_channel = 1
bsda2.disabled = False
bsda2.light_enabled = True
bsda2.temperature_enabled = True
bsda2.voltage_enabled = True

bsda_disabled = BsdaSettings()
bsda_disabled.disabled = True

left = EbiSettings()
left.frame_reader_framing_type = FramingType.SUM_SQ
left.frame_reader_period_ms = 15
left.temperature_reader_period_ms = 30000
left.voltage_reader_period_ms = 33000
left.raw_board = 0
left.bsda_settings[0] = bsda2
left.bsda_settings[1] = bsda2
left.bsda_settings[2] = bsda2
left.ntp_period_m = 15
left.log_uart = True
left.log_level = 2

right = EbiSettings()
right.frame_reader_framing_type = FramingType.SUM_SQ
right.frame_reader_period_ms = 15
right.temperature_reader_period_ms = 30000
right.voltage_reader_period_ms = 33000
right.raw_board = 1
right.bsda_settings[0] = bsda_disabled
right.bsda_settings[1] = bsda_disabled
right.bsda_settings[2] = bsda_disabled
right.log_uart = True
right.log_level = 2

cdm = PyCDM("127.0.0.1")
q = cdm.reg_msg("SYSTEM")

run = True
def trigger():
    while True:
        print(q.get_msg())
    #global run
    #run = False
        time.sleep(0.5)
        #print(cdm.bcg.get_info())
    #print(cdm.bcg.get_state())
    #print(cdm.bcg.get_info())


t = threading.Thread(target=trigger)
t.start()

print(cdm.ebi.connect())
print(cdm.bcg.get_info())
cdm.configure(left, right)
cdm.start_acq()
input("ASD")
a = 0
while run:
    cdm.start_acq()
    time.sleep(0.1)
    cdm.stop_acq()

print("Joinin")
t.join()
print("Closing")
cdm.close()
