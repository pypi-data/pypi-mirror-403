import asyncio
import logging
from asyncio import Queue, QueueShutDown, StreamReader, StreamWriter, Task
from collections.abc import Callable
from typing import TYPE_CHECKING

from pax25.ax25.frame import Frame
from pax25.ax25.protocols import Assembler
from pax25.interfaces.kiss.constants import KISS_CMD_DATA
from pax25.interfaces.kiss.protocol import (
    default_frame_disassemblers,
    filter_kiss_frames,
    kiss_command,
)
from pax25.interfaces.types import Interface, ResolvedConnectionSpec, TCPKISSSettings
from pax25.utils import cancel_all

if TYPE_CHECKING:  # pragma: no cover
    from pax25.station import Station


logger = logging.getLogger(__name__)

DEFAULT_PORT = 7002
DEFAULT_ADDRESS = "127.0.0.1"


class TCPKISSInterface(Interface[TCPKISSSettings]):
    """
    Interface for connecting to TCP-hosting TNCs.
    """

    type = "KISSOverTNC"
    connection: TCPKISSConnection | None

    def __init__(
        self,
        name: str,
        settings: TCPKISSSettings,
        station: Station,
    ) -> None:
        """
        Initialize the Interface.
        """
        self.name = name
        self._settings = settings
        self.station = station
        self.shutting_down = False
        self.connection = None

    def build_connection(self, delay: int = 0) -> None:
        """
        Set up the connection object that will be sending and receiving frames.
        """
        self.connection = TCPKISSConnection(
            remote_tnc=ResolvedConnectionSpec(
                host=self._settings.get("host", DEFAULT_ADDRESS),
                port=self._settings.get("port", DEFAULT_PORT),
            ),
            interface=self,
            close_callback=self.connection_closed,
            delay=delay,
        )

    def connection_closed(self, connection: TCPKISSConnection) -> None:
        """
        Callback for closing the TCP connection.
        """
        if self.shutting_down:
            # Do nothing, this will be cleaned up elsewhere.
            return
        # Need to retry.
        self.start(delay=self.settings.get("retry_delay", 5))

    def start(self, delay: int = 0) -> None:
        """
        Set up the loops.
        """
        self.shutting_down = False
        self.build_connection(delay=delay)

    def send_frame(self, frame: Frame) -> None:
        """
        Send a frame out to all the connections which are listening.
        """
        if self.connection:
            self.connection.send_frame(frame)

    @property
    def listening(self) -> bool:
        """
        Returns true if we are connected to the TNC.
        """
        return bool(
            self.connection
            and self.connection.writer
            and not self.connection.writer.is_closing()
        )

    @property
    def sudo(self) -> bool:
        """
        Randos over the air shouldn't be superusers.
        """
        return False

    @property
    def gateway(self) -> bool:
        return self.settings.get("gateway", True)

    async def reload_settings(self, settings: TCPKISSSettings) -> None:
        """
        Reload interface settings.
        """
        await self.shutdown()
        self._settings = settings
        self.shutting_down = False
        self.start()

    async def shutdown(self) -> None:
        """
        Close out all connections.
        """
        self.shutting_down = True
        if self.connection:
            await self.connection.close()
            self.connection = None


class TCPKISSConnection:
    send_queue: Queue[tuple[Assembler, int]]
    remote_tnc: ResolvedConnectionSpec

    def __init__(
        self,
        *,
        remote_tnc: ResolvedConnectionSpec,
        interface: TCPKISSInterface,
        reader: StreamReader | None = None,
        writer: StreamWriter | None = None,
        close_callback: Callable[[TCPKISSConnection], None],
        delay: int = 0,
    ):
        self.remote_tnc = remote_tnc
        self.interface = interface
        self.reader = reader
        self.writer = writer
        self.send_queue: Queue[tuple[Assembler, int]] = Queue()
        self._connect_future: Task[None] | None = None
        self._read_loop: Task[None] | None = None
        self._write_loop: Task[None] | None = None
        self.initialize_connection(delay)
        self.close_callback = close_callback

    async def close(self) -> None:
        """
        Close the connection.
        """
        await cancel_all((self._connect_future, self._read_loop, self._write_loop))
        self.send_queue.shutdown(immediate=True)
        if self.writer:
            self.writer.close()
        self.writer, self.reader = None, None
        self.close_callback(self)

    async def read_loop(self) -> None:
        """
        Read loop for TCP connection.
        """
        reader = self.reader
        assert reader

        try:
            async for frame in filter_kiss_frames(
                lambda: reader.read(1),
                {Frame},
                get_disassemblers=default_frame_disassemblers,
            ):
                self.interface.station.frame_router.process_frame(self.interface, frame)
        except ConnectionResetError:
            pass
        asyncio.ensure_future(self.close())

    async def write_loop(self) -> None:
        """
        Write loop for TCP connection.
        """
        try:
            while item := await self.send_queue.get():
                [frame, command] = item
                writer = self.writer
                assert writer
                try:
                    writer.write(kiss_command(command, 0, frame.assemble()))
                    await writer.drain()
                except OSError:
                    # Awaiting will Cancel this task before it finishes.
                    asyncio.ensure_future(self.close())
                    return
        except QueueShutDown:
            # Awaiting will kill Cancel this task before it finishes.
            asyncio.ensure_future(self.close())

    def send_frame(self, frame: Assembler, command: int = KISS_CMD_DATA) -> None:
        """
        Sends a frame to this TCP connection.
        """
        self.send_queue.put_nowait((frame, command))

    def start_loops(self) -> None:
        """
        Start up the loops for communicating back and forth.
        """
        self._read_loop = asyncio.ensure_future(self.read_loop())
        self._write_loop = asyncio.ensure_future(self.write_loop())

    def initialize_connection(self, delay: int = 0) -> None:
        """
        Initialize the connection to the TCP-based TNC.
        """
        self._connect_future = asyncio.ensure_future(self._initialize_connection(delay))

    async def _initialize_connection(self, delay: int = 0) -> None:
        """
        Internal process used by initialize_connection to perform its work.
        """
        self.send_queue = Queue()
        ip = self.remote_tnc.host
        port = self.remote_tnc.port
        await asyncio.sleep(delay)
        future = asyncio.open_connection(ip, port)
        try:
            self.reader, self.writer = await asyncio.wait_for(future, timeout=5)
            logger.debug(f"({self.interface.name}) Connected to {ip}:{port}")
        except (TimeoutError, ConnectionRefusedError) as err:
            logger.error(
                f"({self.interface.name}) Failed connecting to {ip}:{port}. "
                f"{err.__class__.__name__}: {err}"
            )
            await self.close()
            return
        self.start_loops()
