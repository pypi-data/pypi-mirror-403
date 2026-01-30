#pragma once

#include <string>
#include <string_view>
#include <mutex>

#include <ifae/libs.hpp>
#include <nlohmann/json.hpp>
#include <zmq.hpp>

using json = nlohmann::json;

class BaseExternalZmq {
  public:
    virtual void start() = 0;
    virtual void close() = 0;

  protected:
    zmq::context_t _ctxt{1};
    spdlogger _log{NewLogger("zmq_comm")};
};

class AsyncZmqServer : public BaseExternalZmq {
  public:
    void start() final;
    void close() final;
    void publish(const std::string_view&, const std::string_view&);
    void publish(std::string&&);

  private:
    zmq::socket_t _pub{_ctxt, zmq::socket_type::pub};
    std::mutex _mutex;
};

class AsyncClient : public BaseExternalZmq {
  public:
    explicit AsyncClient(const std::string&);
    void start() final;
    void close() final;
    void subscribe(const std::string_view&);
    std::string recv();

  private:
    const std::string _addr;
    zmq::socket_t _sock{_ctxt, zmq::socket_type::sub};
};

class CmdServer : public BaseExternalZmq {
  public:
    void start() final;
    void close() final;
    json readReq();
    void sendRep(json&&);

  private:
    zmq::socket_t _sock{_ctxt, zmq::socket_type::rep};
};

class CmdClient : public BaseExternalZmq {
  public:
    explicit CmdClient(const std::string&);
    void start() final;
    void close() final;
    void sendCmd(json&&);
    json readResp();

  private:
    const std::string _addr;
    zmq::socket_t _sock{_ctxt, zmq::socket_type::rep};
};
