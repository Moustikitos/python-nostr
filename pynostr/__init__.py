# -*- coding: utf-8 -*-
"""
**`pynostr`** aims to provide a simple python interface to interact with nostr
environment.

```python
>>> from pynostr import event
>>> e = event.Event.text_note("Hello nostr !").sign()
Type or paste your passphrase >
>>> e.send_to("wss://relay.nostr.info")
['OK', '2781d70bd1497a8db1ac381262de29841d44fd88d387f2725d5e5eb7871d28c9', Tru\
e, '']
```
"""

import os
import json
import websockets

from collections import namedtuple
from pynostr import bech32

#: Contact is defined by a public key, a relay and a petname
Contact = namedtuple('Contact', 'pubkey relay petname')


class Bech32DecodeError(Exception):
    """Exception used for unsuccessful bech32 processing"""


async def send_event(event: dict, uri: str) -> list:
    """
Push single event to a single relay and return responses.

Args:
    event (dict): the event given as a python dict.
    uri (str): relay uri.

Returns:
    list: relay response as python list.
"""
    async with websockets.connect(uri) as ws:
        req = json.dumps(["EVENT", event], separators=(",", ":"))
        await ws.send(req)
        resp = await ws.recv()
        result = json.loads(resp)
    return result


def dump_contact(name: str, *contacts) -> None:
    new_pubkey = [c[0] for c in contacts]
    filename = os.path.join(os.path.dirname(__file__), ".contact", name)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if os.path.exists(filename):
        with open(filename, "r") as _in:
            for ctc in json.loads(_in.read()):
                if ctc[0] not in new_pubkey:
                    contacts += (Contact(*ctc), )
    with open(filename, "w") as out:
        out.write(json.dumps(list(contacts), indent=2))


def load_contact(name: str) -> None:
    filename = os.path.join(os.path.dirname(__file__), ".contact", name)
    if os.path.exists(filename):
        with open(filename, "r") as _in:
            contacts = [Contact(*ctc) for ctc in json.loads(_in.read())]
        return contacts
    return []


def to_bech32(prefix: str, hexa: str):
    converted_bits = bech32.convertbits(bytes.fromhex(hexa), 8, 5)
    return bech32.bech32_encode(prefix, converted_bits, bech32.Encoding.BECH32)


def from_bech32(b32: str):
    data, success = bech32.bech32_decode(b32)[1:]
    if success:
        return bytearray(bech32.convertbits(data, 5, 8))[:-1].hex()
    else:
        raise Bech32DecodeError()


def bech32_puk(pubkey: str) -> str:
    """
Return a nostr public key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    pubkey (str): public key as hex string

Returns:
    str: nostr public key
"""
    return to_bech32("npub", pubkey)


def bech32_prk(prvkey: str) -> str:
    """
Return a nostr private key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    prvkey (str): private key as hex string

Returns:
    str: nostr private key
"""
    return to_bech32("nsec", prvkey)


def bech32_nid(noteid: str) -> str:
    """
Return a nostr event id according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    noteid (str): event id as hex string

Returns:
    str: nostr event id
"""
    return to_bech32("note", noteid)
