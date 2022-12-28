<a id="pynostr.client"></a>

# pynostr.client

This module provides a simple text client to subscribe to a specific relay.

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
Sending and receiving is possible until unsubscritpion.

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

