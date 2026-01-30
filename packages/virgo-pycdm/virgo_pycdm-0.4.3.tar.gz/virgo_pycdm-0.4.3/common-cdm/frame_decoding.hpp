#pragma once

#include <any>
#include <array>
#include <sstream>
#include <string>
#include <variant>
#include <vector>

using FrameBuffer = std::string;
//using FrameStruct =
//std::variant<full_frame_t, sum_frame_t, raw_frame_t, histogram_frame_t, test_frame_t, sum_sq_frame_t>;
using FrameStruct = std::any;

#if 0
class BaseFrame {
  public:
    virtual uint64_t getTimestamp() = 0;
    virtual std::any getData() = 0;

  private:
};

class FullFrame : public BaseFrame {
  public:
    FullFrame(const full_frame_t&& f) : _frame{std::move(f)} {}

    uint64_t getTimestamp() final {
        return _frame.timestamp;
    }

    std::any getData() final {
        return _frame;
    }

  private:
    const full_frame_t _frame;
};

class SumFrame : public BaseFrame {
  public:
    SumFrame(const sum_frame_t&& f) : _frame{std::move(f)} {}

    uint64_t getTimestamp() final {
        return _frame.timestamp;
    }

    std::any getData() final {
        return _frame;
    }

  private:
    const sum_frame_t _frame;
};

class RawFrame : public BaseFrame {
  public:
    RawFrame(const raw_frame_t&& f) : _frame{std::move(f)} {}

    uint64_t getTimestamp() final {
        return _frame.timestamp;
    }

    std::any getData() final {
        return _frame;
    }

  private:
    const raw_frame_t _frame;
};
#endif

class BaseDecoder {
  public:
    explicit BaseDecoder(const FrameBuffer&&);
    virtual ~BaseDecoder() = default;

    // Function mainly used for python interface
    template <typename T> T readFrame() {
        return readFrameStruct<T>();
    }

    FrameStruct readAnyFrame();
    std::vector<FrameStruct> readAllFrames();

    virtual std::array<EbiSettings, 2> getBaffleSettings() const;
    AsyncHeader getHeader() const;

    bool isEof() const;

  protected:
    void decodeAbiVer();
    void decodeAsyncHeader();
    void decodeBaffleSettings();

  private:
    template <typename T> T readFrameStruct();

    std::istringstream _frame_reader;

    std::array<EbiSettings, 2> _baffle_settings{};
    AsyncHeader _header{};
    uint8_t _abi{};
};

class FileDecoder : public BaseDecoder {
  public:
    explicit FileDecoder(const FrameBuffer&&);
    void decodeAsyncHeader();
};

class FrameDecoder : public BaseDecoder {
  public:
    explicit FrameDecoder(const FrameBuffer&&);
    std::array<EbiSettings, 2> getBaffleSettings() const final;
};
