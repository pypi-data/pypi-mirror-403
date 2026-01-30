import queue
import logging
from threading import Thread

import zmq.error

from .comm import ZmqAsyncConn

log = logging.getLogger(__name__)

Msg = tuple[str, bytes]


class MsgReg(queue.Queue[Msg]):

    def __init__(self, i: str) -> None:
        super().__init__()
        self._id = i

    def id_match(self, i: str) -> bool:
        return self._id == i[0:len(self._id)]

    def add_msg(self, msg: Msg) -> None:
        self.put(msg)

    def get_msg(self) -> bytes:
        return self.get(block=True)[1]


class DataManager:

    def __init__(self, addr: str) -> None:
        self._cdm_async = ZmqAsyncConn(addr)

        self._thread = Thread(target=self._frame_reader)
        self._thread.start()

        self._msg_reg: list[MsgReg] = []

    def close(self) -> None:
        log.info("Closing DataManager")
        self._cdm_async.disconnect()
        self._thread.join()

    def register(self, s: str) -> MsgReg:
        reg = MsgReg(s)
        self._msg_reg.append(reg)
        self._cdm_async.subscribe(s)
        return reg

    def _frame_reader(self) -> None:
        log.info("FRAME READER STARTED")
        try:
            while True:
                m = self._cdm_async.recv_msg()
                for i in self._msg_reg:
                    if i.id_match(m[0]):
                        i.add_msg(m)
        except zmq.error.ContextTerminated:
            log.warning("Exiting from frame reader")
