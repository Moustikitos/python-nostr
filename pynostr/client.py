# -*- coding: utf-8 -*-

"""
This module provides a simple text client to subscribe to a specific relay.

```python
>>> from pynostr import client
>>> c = client.BaseThread("wss://relay.nostr.info")
>>> c.subscribe(kinds=[0, 1, 3], limit=5)
----- BEGIN -----
[...]
```

During a subscription, it is possible to send events.

```python
>>> c.send_event(kind=1, content="hello nostr !")
Type or paste your passphrase >
<dce2c201607e803384f51574c6a472a58fcfaf49bf32944c2e6caa9a72b87dad>[23:02:12](     1): hello nostr !
['OK', '1c84a86b44716dbc66fb739ded71bd75213acb2f6d23a88e4a44dac09b277edb', True, '']
```


```python
>>> c.unsubscribe()
[...]
----- END -----
```
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


class AlreadySubcribed(Exception):
    """Exception used if a subscription is already running"""


if sys.platform == "win32":
    # enable the use of print_during_input with windows command
    # copied from from websockets.__main__.py
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


# copied from from websockets.__main__.py
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
Args:
    uri (str): .
    timeout (int): .

Attributes:
    uri (str): .
    timeout (str): .
    response (int): .
    request (int): .
    loop (list): .
"""

    def __init__(self, uri: str, timeout: int = 5) -> None:
        self.uri = uri
        self.timeout = timeout
        self.response = queue.Queue()
        self.request = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.__filter: filter.Filter
        self.__id = None
        self.__stop = threading.Event()
        self.__skip = 0

    def subscribe(self, cnf: dict = {}, **kw) -> None:
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
        self.__skip = 0
        # start response daemon
        self.resp_daemon = threading.Thread(target=self.manage_resp)
        self.resp_daemon.setDaemon(True)
        self.resp_daemon.start()
        # start websocket loop daemon
        self.lstn_daemon = threading.Thread(
            target=self.loop.run_until_complete,
            args=(self.loop.create_task(self.__loop()), )
        )
        self.lstn_daemon.setDaemon(True)
        self.lstn_daemon.start()

    async def __send_event(self) -> bool:
        if not self.request.empty():
            req = self.request.get()
            if req[0] == "CLOSE":
                self.__stop.set()
            await asyncio.wait_for(
                self.__ws.send(json.dumps(req)), timeout=self.timeout
            )

    async def __loop(self) -> None:
        print_during_input("----- BEGIN -----")
        while not self.__stop.is_set():
            try:
                async with websockets.connect(self.uri) as ws:
                    # store current websocket to be used in __close_check
                    # for unsubscribing
                    self.__ws = ws
                    # subscribe according to self.__filter
                    await ws.send(
                        json.dumps(["REQ", self.__id, self.__filter.apply()])
                    )
                    # self.__skip is set to self.limit after the first
                    # exception so first events defined by self.limit are not
                    # repeating endlessly.
                    for i in range(self.__skip):
                        await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                    # enter dialog loop
                    while not self.__stop.is_set():
                        self.response.put(
                            await asyncio.wait_for(
                                ws.recv(), timeout=self.timeout
                            )
                        )
                        await(self.__send_event())
            except websockets.ConnectionClosed:
                continue
            except TimeoutError:
                continue
            finally:
                self.__skip = self.__filter.limit
        # terminate self.resp_daemon
        self.response.put("STOP")

    def manage_resp(self) -> None:
        exit = False
        while not exit:
            data = self.response.get()
            if data == "STOP":
                exit = True
                print_during_input("----- END -----")
            else:
                self.apply(json.loads(data))

    def apply(self, data: list):
        if data[0] == "EVENT":
            evnt = data[-1]
            prefix = "<%s>[%s](% 6d): " % (
                evnt["pubkey"],
                datetime.fromtimestamp(evnt["created_at"]).strftime("%X"),
                evnt["kind"]
            )
            content = textwrap.wrap(
                evnt["content"], width=100, break_on_hyphens=True
            )
            if content:
                print_during_input(prefix + content[0])
                if len(content) > 1:
                    padding = " " * len(prefix)
                    for line in [li for li in content[1:] if li != ""]:
                        print_during_input(padding + line)
        else:
            print_during_input(data)

    def unsubscribe(self):
        self.request.put(["CLOSE", self.__id])

    def send_event(self, cnf: dict = {}, **kw):
        evnt = event.Event(cnf, **kw).sign(prvkey=kw.get("prvkey", None))
        self.request.put(["EVENT", evnt.__dict__])

    def push_event(self, evnt: event.Event):
        if "sig" not in evnt:
            evnt.sign()
        self.request.put(["EVENT", evnt.__dict__])
