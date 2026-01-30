#pragma once

#include <cstdint>

enum class SM_STATE : uint8_t {
	INITIALIZED,
	OTA_FLASH,
	OTA_TEST,
	ERBI_READY,
	BSDA_READY,
	ACQ,
	ERROR,
};
