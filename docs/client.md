<a id="pynostr.client"></a>

# pynostr.client

This module provides a simple text client for sending/listening to a specfic
relay.

<a id="pynostr.client.AlreadySubcribed"></a>

## AlreadySubcribed Objects

```python
class AlreadySubcribed(Exception)
```

Exception used if a subscription is already running

<a id="pynostr.client.BaseThread"></a>

## BaseThread Objects

```python
class BaseThread()
```

A Simple text client. It allows custom subscription to a specific relay.
Sending and receiving is possible until subscription is over.

**Arguments**:

- `uri` _str_ - the nostr relay url.
- `timeout` _int_ - wait timeout in seconds [default = 5].
- `textwidth` _int_ - text width for the output [default = 100].

**Attributes**:

- `uri` _str_ - the nostr relay url.
- `timeout` _str_ - wait timeout in seconds [default = 5].
- `textwidth` _int_ - text width for the output [default = 100].
- `response` _queue.Queue_ - queue to store relay response.
- `request` _queue.Queue_ - queue to store client requests.
- `loop` _asyncio.BaseEventLoop_ - event loop used to un sending/listening
  process.

**Examples**:

  ```python
  >>> from pynostr import client
  >>> c = client.BaseThread("wss://relay.nostr.info")
  ```

<a id="pynostr.client.BaseThread.subscribe"></a>

#### subscribe

```python
def subscribe(cnf: dict = {}, **kw) -> None
```

Subscribe to relay with custom filtering. See [filter](filter#Filter) class
for basic uses.

**Arguments**:

- `cnf` _dict_ - key-value pairs.
- `**kw` - arbitrary keyword arguments.

**Examples**:

  ```python
  >>> # subscribe to all messages kind 1, 2 or 3 getting the last 5 ones.
  >>> c.subscribe(kinds=[0, 1, 3], limit=5)
  ```

<a id="pynostr.client.BaseThread.apply"></a>

#### apply

```python
def apply(data: list) -> None
```

This function operates with listened data. Data is loaded from json string and
is either `EVENT`, `NOTICE`, `OK` or `EOSE` messages as specified in
[nostr protocol](https://github.com/nostr-protocol/nips#relay-to-client).

**Arguments**:

- `data` _list_ - relay response as python object. First item of data is either
  `EVENT`, `NOTICE`, `OK` or `EOSE` word.

<a id="pynostr.client.BaseThread.unsubscribe"></a>

#### unsubscribe

```python
def unsubscribe() -> None
```

Stop the running subscription. Once listening daemons cleanly exited, a new
subscription is possible. This function sends a `CLOSE` event to stop the
thread cleanly.

**Examples**:

  ```python
  >>> # to close websocket, just unsubscribe
  >>> c.unsubscribe()
  ```

<a id="pynostr.client.BaseThread.send_event"></a>

#### send\_event

```python
def send_event(cnf: dict = {}, **kw) -> None
```

Create and send event during a subscription. See [event](event#Event) class
for basic uses. Event is sent when a slot is available (ie timeout occured or
`recv` completed).

**Arguments**:

- `cnf` _dict_ - key-value pairs.
- `**kw` - arbitrary keyword arguments.

**Examples**:

  ```python
  >>> # During a subscription, it is possible to send events:
  >>> c.send_event(kind=1, content="hello nostr !")
  Type or paste your passphrase >
  [...]
  <dce2c[...]87dad>[23:02:12](     1):
  hello nostr !
  ['OK', '1c84a[...]77edb', True, '']
  ```

