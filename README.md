
# `pynostr`

This python package aims to provide a simple python interface to interact with
nostr environment.

```python
>>> from pynostr import event
>>> e = event.Event.text_note("Hello nostr !").sign()
Type or paste your passphrase >
>>> e.send_to("wss://relay.nostr.info")
['OK', '2781d[...]d28c9', True, '']
```

## Documentation

**[Read it on github](/docs)**

This doc is generated using [pydoc-markdown](
https://github.com/NiklasRosenstein/pydoc-markdown
) upon python docstring written
following [Google docstring recomendation](
    https://gist.github.com/redlotus/3bc387c2591e3e908c9b63b97b11d24e
)

## NIP implementation

<!-- https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716 -->

### Client

* [x] NIP 01
* [x] NIP 13
* [x] NIP 19
