#include <utility>

#include <fmt/format.h>

#include "common/cmd.hpp"

#include "frame_decoding.hpp"

BaseDecoder::BaseDecoder(const FrameBuffer&& f) : _frame_reader{std::move(f)} {}

FrameStruct BaseDecoder::readAnyFrame() {
    switch(_header.type) {
        case FRAMING_T::FULL: return readFrameStruct<full_frame_t>();
        case FRAMING_T::SUM: return readFrameStruct<sum_frame_t>();
        case FRAMING_T::RAW: return readFrameStruct<raw_frame_t>();
        case FRAMING_T::HISTOGRAM: return readFrameStruct<histogram_frame_t>();
        case FRAMING_T::TEST: return readFrameStruct<test_frame_t>();
        case FRAMING_T::SUM_SQ: return readFrameStruct<sum_sq_frame_t>();
    }

    auto msg = fmt::format("Header type not handled: {}", static_cast<unsigned>(_header.type));
    throw std::runtime_error(msg);
}

std::vector<FrameStruct> BaseDecoder::readAllFrames() {
    std::vector<FrameStruct> frames;
    while(_header.count > 0) frames.emplace_back(readAnyFrame());

    return frames;
}

std::array<EbiSettings, 2> BaseDecoder::getBaffleSettings() const {
    return _baffle_settings;
}

AsyncHeader BaseDecoder::getHeader() const {
    return _header;
}

bool BaseDecoder::isEof() const {
    return _frame_reader.eof();
}

// protected methods

void BaseDecoder::decodeAbiVer() {
    _frame_reader.read((char*)&_abi, sizeof(_abi));
}

void BaseDecoder::decodeAsyncHeader() {
    _frame_reader.read((char*)&_header, sizeof(_header));
}

void BaseDecoder::decodeBaffleSettings() {
    _frame_reader.read((char*)&_baffle_settings, sizeof(_baffle_settings));
}

// private methods

template <typename T> T BaseDecoder::readFrameStruct() {
    T f;
    _frame_reader.read((char*)&f, sizeof(T));
    _header.count--;
    return f;
}

// File Decoder class

// TODO: Allow to pass a string and handle the I/O in this class
FileDecoder::FileDecoder(const FrameBuffer&& buf) : BaseDecoder(std::move(buf)) {
    decodeAbiVer();
    decodeBaffleSettings();
    decodeAsyncHeader();
}

void FileDecoder::decodeAsyncHeader() {
    BaseDecoder::decodeAsyncHeader();
}

// Frame Decoder class

FrameDecoder::FrameDecoder(const FrameBuffer&& buf) : BaseDecoder(std::move(buf)) {
    decodeAsyncHeader();
}

std::array<EbiSettings, 2> FrameDecoder::getBaffleSettings() const {
    throw std::runtime_error("FrameDecoder doesn't contains baffle settings");
}

// Needed because a bug on GCC. On newer versions of GCC is not required.
template full_frame_t BaseDecoder::readFrameStruct<full_frame_t>();
template sum_frame_t BaseDecoder::readFrameStruct<sum_frame_t>();
template raw_frame_t BaseDecoder::readFrameStruct<raw_frame_t>();
template histogram_frame_t BaseDecoder::readFrameStruct<histogram_frame_t>();
template sum_sq_frame_t BaseDecoder::readFrameStruct<sum_sq_frame_t>();
