import socket

import zmq

context: zmq.Context = zmq.Context()


class ZmqSyncConn:
    def __init__(self, cdm_addr: str) -> None:
        t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        t.settimeout(2)
        if t.connect_ex((cdm_addr, 32000)) != 0:
            raise Exception("CDM doesn't seems to be running")
        self._sock = context.socket(zmq.REQ)
        self._sock.connect("tcp://{}:32000".format(cdm_addr))

    def send(self, s: str) -> None:
        self._sock.send_string(s)

    def recv(self) -> bytes:
        return self._sock.recv()


class ZmqAsyncConn:
    def __init__(self, cdm_addr: str) -> None:
        self._sock = context.socket(zmq.SUB)
        self._ctxt = self._sock.connect("tcp://{}:32001".format(cdm_addr))

    def recv_msg(self) -> tuple[str, bytes]:
        msg_id = self._sock.recv().decode()
        msg = self._sock.recv()
        return msg_id, msg

    def subscribe(self, topic: str) -> None:
        self._sock.setsockopt_string(zmq.SUBSCRIBE, topic)

    def disconnect(self) -> None:
        global context
        context.destroy()
        context = zmq.Context()
