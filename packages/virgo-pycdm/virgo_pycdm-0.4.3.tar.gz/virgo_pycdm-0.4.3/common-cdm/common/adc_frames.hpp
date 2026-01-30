#include <array>
#include <cstdint>

#pragma once

#define TEST_FRAME_DATA_SIZE 250

inline constexpr unsigned k_devices = 2;
inline constexpr unsigned k_channels_per_device = 10;
inline constexpr unsigned k_channels = k_devices * k_channels_per_device;
inline constexpr unsigned k_samples_per_rawframe = 3000;
inline constexpr unsigned k_histogram_bins = 12;

/* Test Frame */
struct __attribute__((__packed__)) test_frame_t {
    uint64_t timestamp;
    uint8_t data[TEST_FRAME_DATA_SIZE];
};

/* Full Frame */
struct __attribute__((__packed__)) full_frame_channel_t {
    uint32_t sum;
    uint16_t min;
    uint16_t max;
};

struct __attribute__((__packed__)) full_frame_t {
    uint64_t timestamp;
    uint16_t count;
    std::array<full_frame_channel_t, k_channels> data;
};

/* Sum Frame */
struct __attribute__((__packed__)) sum_frame_channel_t {
    uint32_t sum;
};

struct __attribute__((__packed__)) sum_frame_t {
    uint64_t timestamp;
    uint16_t count;
    std::array<sum_frame_channel_t, k_channels> data;
};

/* Raw Frame */
struct __attribute__((__packed__)) raw_frame_data_t {
    uint16_t value;
};

struct __attribute__((__packed__)) raw_frame_t {
    uint64_t timestamp;
    std::array<raw_frame_data_t, k_samples_per_rawframe> data;
};

/* Histogram Frame */
struct __attribute__((__packed__)) histogram_frame_channel_t {
    std::array<uint8_t, k_histogram_bins> bins;
};

struct __attribute__((__packed__)) histogram_frame_t {
    uint64_t timestamp;
    std::array<histogram_frame_channel_t, k_channels> data;
};

// Squared sum frame
struct __attribute__((__packed__)) sum_sq_frame_channel_t {
    uint32_t sum;
    uint64_t sum_sq;
};

struct __attribute__((__packed__)) sum_sq_frame_t {
    uint64_t timestamp;
    uint16_t count;
    std::array<sum_sq_frame_channel_t, k_channels> data;
};
