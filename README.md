
# `pynostr`

This python package aims to provide a simple interface to interact with nostr relays.

```python
>>> from pynostr import event
>>> e = event.Event.text_note("Hello nostr !").sign()
Type or paste your passphrase >
>>> e.send_to("wss://relay.nostr.info")
['OK', '995b2c845315bd47d43cdff7a6f76f834943afa07144655247b8ceab6d6d2ecd', True, '']
```

## Basic text client subscriber

```python
>>> from pynostr import client
>>> c = client.BaseThread("wss://relay.nostr.info")
>>> c.subscribe(kinds=[0, 1, 3], limit=5)
```

![Console client](docs/img/client.png)

## Documentation

**[Read it on github](/docs)**

This doc is generated using [pydoc-markdown](
https://github.com/NiklasRosenstein/pydoc-markdown
) upon python docstring written
following [Google docstring recommendation](
    https://gist.github.com/redlotus/3bc387c2591e3e908c9b63b97b11d24e
)

## NIP implementation

<!-- https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716 -->

### Client

* [x] NIP 01
* [x] NIP 13
* [x] NIP 19
