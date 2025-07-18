import asyncio
import io
import threading
from asyncio import AbstractEventLoop, transports
from threading import get_ident

from hazelcast.connection import Connection

_BUFFER_SIZE = 128000


class AsyncioReactor:

    def __init__(self, loop=None):
        # TODO: pass loop as an argument
        self._is_live = False
        if loop:
            self._loop = loop
        else:
            self._loop = asyncio.get_running_loop()
            # try:
            #     self._loop = asyncio.get_running_loop()
            # except RuntimeError:
            #     self._loop = asyncio.new_event_loop()
        self._ident = None
        self._thread = None

    def add_timer(self, delay, callback):
        return self._loop.call_later(delay, callback)

    def start(self):
        t = threading.Thread(target=self._asyncio_loop, daemon=True, name="hazelcast_python_client_reactor")
        t.start()
        self._thread = t
        self._ident = t.ident
        self._is_live = True

    def shutdown(self):
        if not self._is_live:
            return
        # TODO: mutex
        self._is_live = False
        self._loop.stop()
        print("RUNNING?", self._loop.is_running())
        # self._loop.close()
        if self._ident != get_ident():
            pass
            # self._thread.join()

    def connection_factory(
        self, connection_manager, connection_id, address, network_config, message_callback
    ):
        # TODO: pass the reactor to the connection, so bytes_received and bytes_sent are updated
        return AsyncioConnection.create_and_connect(
            self._loop, connection_manager, connection_id, address, network_config, message_callback,
        )

    def _asyncio_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()


class AsyncioConnection(Connection):

    def __init__(self, loop, connection_manager, connection_id, address, config, message_callback):
        super().__init__(connection_manager, connection_id, message_callback)
        self._loop = loop
        self._proto = None

    @classmethod
    async def create_and_connect(cls, loop, connection_manager, connection_id, address, config, message_callback):
        this = cls(loop, connection_manager, connection_id, address, config, message_callback)
        await this.connect(address.host, address.port)
        return this

    async def connect(self, host, port):
        def factory():
            return HazelcastProtocol(loop, self._reader, self._update_read_time, self._update_write_time)

        loop = asyncio.get_running_loop()
        res = await loop.create_connection(factory, host=host, port=port)
        _sock, self._proto = res

    def _write(self, buf):
        self._proto.write(buf)

    def _inner_close(self):
        self._proto.close()

    def _update_read_time(self, time):
        self.last_read_time = time

    def _update_write_time(self, time):
        self.last_write_time = time


class HazelcastProtocol(asyncio.BufferedProtocol):

    send_buffer_size = _BUFFER_SIZE

    def __init__(self, loop: AbstractEventLoop, reader, update_read_time, update_write_time):
        self._loop = loop
        self._update_read_time = update_read_time
        self._update_write_time = update_write_time
        self._transport = None
        self.start_time = None
        self._write_buf = io.BytesIO()
        self._write_buf_size = 0
        self._recv_buf = None
        self._alive = True
        self._reader = reader

    def connection_made(self, transport: transports.Transport):
        self._transport = transport
        self.start_time = self._loop.time()
        self.write(b"CP2")
        self._loop.call_soon(self._write_loop)

    def connection_lost(self, exc):
        self._alive = False
        return False

    def close(self):
        self._transport.close()

    def write(self, buf):
        self._write_buf.write(buf)
        self._write_buf_size += len(buf)

    def get_buffer(self, sizehint):
        if self._recv_buf is None:
            buf_size = max(sizehint, _BUFFER_SIZE)
            self._recv_buf = memoryview(bytearray(buf_size))
        return self._recv_buf

    def buffer_updated(self, nbytes):
        recv_bytes = self._recv_buf[:nbytes]
        self._update_read_time(self._loop.time())
        self._reader.read(recv_bytes)
        if self._reader.length:
            self._reader.process()

    def eof_received(self):
        self._alive = False

    def _do_write(self):
        if not self._write_buf_size:
            return
        buf_bytes = self._write_buf.getvalue()
        self._transport.write(buf_bytes[:self._write_buf_size])
        self._update_write_time(self._loop.time())
        self._write_buf.seek(0)
        self._write_buf_size = 0

    def _write_loop(self):
        self._do_write()
        self._loop.call_later(0.01, self._write_loop)

