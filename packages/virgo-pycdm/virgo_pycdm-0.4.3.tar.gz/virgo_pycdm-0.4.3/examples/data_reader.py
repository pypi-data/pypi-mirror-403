import json
from pycdm import PyCDM, BsdaSettings, FramingType, EbiSettings

cdm = PyCDM("127.0.0.1")
cdm.ebi.connect()

# To read data only from one side or a specific BSDA use
# DATA.TEMP.R or DATA.TEMP.L (to read only from left or right side)
# or
# DATA.TEMP.RN where N can be 0,1,2
# It also works the same for DATA.FRAME
temperature_msg_queue = cdm.reg_msg("DATA.TEMP")
data_msg_queue = cdm.reg_msg("DATA.FRAME")
# Other values that can be registered are:
#   PS.VLT
#   PS.AMP
#   LAST_COMM
#   DISK


bsda = BsdaSettings()
bsda.framing = FramingType.FULL
bsda.frame_duration_us = 1000
bsda.temperature_period_ms = 90000
#bsda.adc_shadow = [0xf9f, 0xf9f]
bsda.adc_shadow = [0xf9f0, 0xf9f0]
bsda.log_uart = True
bsda.log_level = 3
bsda.raw_adc = 1
bsda.raw_channel = 1
bsda.disabled = False
bsda.light_enabled = False
bsda.temperature_enabled = True

bsda_disabled = BsdaSettings()
bsda_disabled.disabled = True

left = EbiSettings()
left.frame_reader_framing_type = FramingType.FULL
left.frame_reader_period_ms = 15
left.temperature_reader_period_ms = 100
left.raw_board = 0
left.bsda_settings[0] = bsda_disabled
left.bsda_settings[1] = bsda_disabled
left.bsda_settings[2] = bsda_disabled
left.log_uart = True
left.log_level = 3

right = EbiSettings()
right.frame_reader_framing_type = FramingType.FULL
right.frame_reader_period_ms = 15
right.temperature_reader_period_ms = 100
right.raw_board = 1
right.bsda_settings[0] = bsda
right.bsda_settings[1] = bsda_disabled
right.bsda_settings[2] = bsda_disabled
right.log_uart = True
right.log_level = 3

cdm.configure(left, right)

while True:
    j = json.loads(temperature_msg_queue.get_msg())
    print(j)
    #print("Board: {}, I2C: {}, PT100: {}".format(j["board"], j["i2c"], j["pt100"]))

cdm.close()
