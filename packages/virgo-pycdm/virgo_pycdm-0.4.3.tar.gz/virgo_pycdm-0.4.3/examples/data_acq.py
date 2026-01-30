from pycdm import PyCDM, BsdaSettings, FramingType, EbiSettings

# PyCDM constructor accepts an optional argument as a string
# this argument is the IP of the CDM server.
# eg: cdm = PyCDM("127.0.0.1)
cdm = PyCDM("172.16.17.247")

cdm.ebi.connect()


bsda = BsdaSettings()
bsda.framing = FramingType.FULL
bsda.frame_duration_us = 1000
bsda.temperature_period_ms = 30000
bsda.adc_shadow = [0xf9f0, 0xf9f0]
bsda.log_uart = True
bsda.log_level = 3
bsda.raw_adc = 1
bsda.raw_channel = 1
bsda.disabled = False
bsda.temperature_enabled = True
bsda.light_enabled = True

bsda_disabled = BsdaSettings()
bsda_disabled.disabled = True

left = EbiSettings()
left.frame_reader_framing_type = FramingType.FULL
left.frame_reader_period_ms = 15
left.temperature_reader_period_ms = 30000
left.raw_board = 0
left.bsda_settings[0] = bsda_disabled
left.bsda_settings[1] = bsda_disabled
left.bsda_settings[2] = bsda_disabled
left.log_uart = True
left.log_level = 3

right = EbiSettings()
right.frame_reader_framing_type = FramingType.FULL
right.frame_reader_period_ms = 15
right.temperature_reader_period_ms = 30000
right.raw_board = 1
right.bsda_settings[0] = bsda
right.bsda_settings[1] = bsda
right.bsda_settings[2] = bsda
right.log_uart = True
right.log_level = 3

cdm.configure(left, right)
cdm.start_acq()
cdm.close()
