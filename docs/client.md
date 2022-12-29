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

<a id="pynostr.client.BaseThread.subscribe"></a>

#### subscribe

```python
def subscribe(cnf: dict = {}, **kw) -> None
```

Subscribe to relay with custom filtering. See [filter](filter#Filter) class
for basic uses.

<a id="pynostr.client.BaseThread.apply"></a>

#### apply

```python
def apply(data: list) -> None
```

This function operates with listened data.

**Arguments**:

- `data` _list_ - relay response as python object.

<a id="pynostr.client.BaseThread.unsubscribe"></a>

#### unsubscribe

```python
def unsubscribe() -> None
```

Stop running subscription. Once listening daemons cleanly exited, a new
subscription is possible.

