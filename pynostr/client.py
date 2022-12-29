# -*- coding: utf-8 -*-

"""
This module provides a simple text client for sending/listening to a specfic
relay.
"""

import os
import sys
import json
import queue
import asyncio
import textwrap
import threading
import websockets

from pynostr import filter, event
from datetime import datetime
from collections import deque
from enum import StrEnum


class Style(StrEnum):
    END = '\33[0m'
    INV = '\33[7m'
    YEL = '\33[33m'
    GRN = '\33[32m'


class AlreadySubcribed(Exception):
    """Exception used if a subscription is already running"""


if sys.platform == "win32":
    # enable the use of print_during_input with windows command
    #: copied from from websockets.__main__.py
    def win_enable_vt100() -> None:
        """
        Enable VT-100 for console output on Windows.

        See also https://bugs.python.org/issue29059.
        """
        import ctypes

        STD_OUTPUT_HANDLE = ctypes.c_uint(-11)
        INVALID_HANDLE_VALUE = ctypes.c_uint(-1)
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x004

        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if handle == INVALID_HANDLE_VALUE:
            raise RuntimeError("unable to obtain stdout handle")

        cur_mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(
            handle, ctypes.byref(cur_mode)
        ) == 0:
            raise RuntimeError("unable to query current console mode")

        # ctypes ints lack support for the required bit-OR operation.
        # Temporarily convert to Py int, do the OR and convert back.
        py_int_mode = int.from_bytes(cur_mode, sys.byteorder)
        new_mode = ctypes.c_uint(
            py_int_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        )

        if ctypes.windll.kernel32.SetConsoleMode(handle, new_mode) == 0:
            raise RuntimeError("unable to set console mode")

    win_enable_vt100()


#: copied from from websockets.__main__.py
def print_during_input(string: str) -> None:
    sys.stdout.write(
        # Save cursor position
        "\N{ESC}7"
        # Add a new line
        "\N{LINE FEED}"
        # Move cursor up
        "\N{ESC}[A"
        # Insert blank line, scroll last line down
        "\N{ESC}[L"
        # Print string in the inserted blank line
        f"{string}\N{LINE FEED}"
        # Restore cursor position
        "\N{ESC}8"
        # Move cursor down
        "\N{ESC}[B"
    )
    sys.stdout.flush()


class BaseThread:
    """
A Simple text client. It allows custom subscription to a specific relay.
Sending and receiving is possible until subscription is over.

Args:
    uri (str): the nostr relay url.
    timeout (int): wait timeout in seconds [default = 5].
    textwidth (int): text width for the output [default = 100].
Attributes:
    uri (str): the nostr relay url.
    timeout (str): wait timeout in seconds [default = 5].
    textwidth (int): text width for the output [default = 100].
    response (queue.Queue): queue to store relay response.
    request (queue.Queue): queue to store client requests.
    loop (asyncio.BaseEventLoop): event loop used to un sending/listening
        process.
"""

    def __init__(
        self, uri: str, timeout: int = 5, textwidth: int = 100
    ) -> None:
        self.uri = uri
        self.timeout = timeout
        self.response = queue.Queue()
        self.request = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.textwidth = textwidth
        self.__filter: filter.Filter
        self.__trace: deque
        self.__id = None
        self.__stop = threading.Event()

    def subscribe(self, cnf: dict = {}, **kw) -> None:
        """
Subscribe to relay with custom filtering. See [filter](filter#Filter) class
for basic uses.
"""
        # check if already runing a subscription
        if hasattr(self, "resp_daemon"):
            if self.resp_daemon.is_alive():
                raise AlreadySubcribed(
                    "subscription %s is already running" % self.__id
                )
        # initialize internal parmeters
        self.__filter = filter.Filter(cnf, **kw)
        self.__id = os.urandom(16).hex()
        self.__stop.clear()
        self.__trace = deque(maxlen=self.__filter.limit)
        # start response daemon
        self.resp_daemon = threading.Thread(target=self.__manage_resp)
        self.resp_daemon.setDaemon(True)
        self.resp_daemon.start()
        # start websocket loop daemon
        self.lstn_daemon = threading.Thread(
            target=self.loop.run_until_complete,
            args=(self.loop.create_task(self.__loop()), )
        )
        self.lstn_daemon.setDaemon(True)
        self.lstn_daemon.start()

    async def __send_event(self) -> None:
        still = True
        if not self.request.empty():
            req = self.request.get()
            if req[0] == "CLOSE":
                self.__stop.set()
                still = False
            await asyncio.wait_for(
                self.__ws.send(json.dumps(req)), timeout=self.timeout
            )
        return still

    async def __loop(self) -> None:
        print_during_input(
            Style.INV + "BEGIN ".rjust(self.textwidth, " ") + Style.END
        )
        while not self.__stop.is_set():
            try:
                async with websockets.connect(self.uri) as ws:
                    # store current websocket to be used in __close_check
                    # for sendings
                    self.__ws = ws
                    # subscribe according to self.__filter
                    await ws.send(
                        json.dumps(["REQ", self.__id, self.__filter.apply()])
                    )
                    while not self.__stop.is_set():
                        # assert is false if a CLOSE request is sent
                        assert await(self.__send_event())
                        self.response.put(
                            await asyncio.wait_for(
                                ws.recv(), timeout=self.timeout
                            )
                        )
            except AssertionError:
                continue
            except websockets.ConnectionClosed:
                continue
            except TimeoutError:
                continue
        # terminate self.resp_daemon
        self.response.put("STOP")

    def __manage_resp(self) -> None:
        exit = False
        while not exit:
            data = self.response.get()
            if data == "STOP":
                exit = True
                print_during_input(
                    Style.INV + "END ".rjust(self.textwidth, " ") + Style.END
                )
            else:
                self.apply(json.loads(data))

    def apply(self, data: list) -> None:
        """
This function operates with listened data.

Arguments:
    data (list): relay response as python object.
"""
        if data[0] == "EVENT":
            evnt = data[-1]

            _id = evnt["id"]
            if _id in self.__trace:
                return
            self.__trace.appendleft(_id)

            prefix = " <%s>[%s](% 6d):" % (
                evnt["pubkey"],
                datetime.fromtimestamp(evnt["created_at"]).strftime("%X"),
                evnt["kind"]
            )
            prefix = prefix.rjust(self.textwidth, "-")
            content = textwrap.wrap(
                evnt["content"], width=self.textwidth, break_on_hyphens=True
            )
            if content:
                print_during_input(prefix)
                for line in content:
                    print_during_input(Style.GRN + line + Style.END)
        else:
            print_during_input(
                Style.YEL + str(data).rjust(self.textwidth, " ") + Style.END
            )

    def unsubscribe(self) -> None:
        """
Stop running subscription. Once listening daemons cleanly exited, a new
subscription is possible.
"""
        self.request.put(["CLOSE", self.__id])

    def send_event(self, cnf: dict = {}, **kw) -> None:
        params = dict(cnf, **kw)
        prvkey = params.pop("prvkey", None)
        evnt = event.Event(**params)
        self.push_event(evnt, prvkey)

    def push_event(self, evnt: event.Event, prvkey=None) -> None:
        if "sig" not in evnt:
            evnt.sign(prvkey)
        self.request.put(["EVENT", evnt.__dict__])
