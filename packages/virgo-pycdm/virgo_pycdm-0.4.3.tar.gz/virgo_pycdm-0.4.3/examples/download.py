from pycdm import PyCDM, BsdaSettings, FramingType, EbiSettings
cdm = PyCDM()
cdm.download_file(2023, 2, 27, 13, "FRAME.1", "/tmp/PYTHON_DOWNLOAD_TEST")
cdm.close()
