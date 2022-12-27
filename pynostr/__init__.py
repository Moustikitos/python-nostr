# -*- coding: utf-8 -*-
"""
This module provides nostr basic functionalities.
"""

import os
import json
import websockets

from collections import namedtuple
from pynostr import bech32

#: Contact is defined by a public key, a relay and a petname. It is implemented
#: as a `namedtuple` with `pubkey`, `relay` and `petname` fieldnames.
#: ```python
#: >>> import pynostr
#: >>> contac = Contact(
#: ...    pubkey=
#: ...      "9aa650df414cc71b37176412aecba987727b6f1b8cd550f40e9ca10b7af5a239",
#: ...    relay="wss://relay.nostr.info",
#: ...    petname="Toon's"
#: ... )
#: >>> print(contact)
#: Contact(pubkey='9aa65[...]5a239', relay='wss:/[...].info', petname="Toon's")
#: ```
Contact = namedtuple('Contact', 'pubkey relay petname')


def dump_contact(name: str, *contacts) -> None:
    """
Store a list of [contact](#pynostr.Contact) as json format. Files are stored in
`<pynostr.__path__[0]>/.contact` folder. Folder `.contact` is created if
needed.

Arguments:
    name (str): filename to be used.
    *contact: variable length of [contact](#pynostr.Contact)
"""
    # get the file path and create folders if needed
    filename = os.path.join(os.path.dirname(__path__[0]), ".contact", name)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # if file already created, load it to avoid loosing them
    if os.path.exists(filename):
        contacts += tuple(
            [
                ctc for ctc in load_contact(name)
                if ctc[0] not in [c[0] for c in contacts]
            ]
        )
    with open(filename, "w") as out:
        out.write(json.dumps(list(contacts), indent=2))


def load_contact(name: str) -> list:
    """
Load a list of [contact](#pynostr.Contact) from a file stored in
`<pynostr.__path__[0]>/.contact` folder. Return an empty list if file or
`.contact` folder do not exist.

Arguments:
    name (str): filename to be used.
Returns:
    list: list of [contact](#pynostr.Contact).
"""
    filename = os.path.join(os.path.dirname(__path__[0]), ".contact", name)
    if os.path.exists(filename):
        with open(filename, "r") as _in:
            contacts = [Contact(*ctc) for ctc in json.loads(_in.read())]
        return contacts
    return []


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


def to_bech32(prefix: str, hexa: str) -> str:
    """
Encode string to a prefixed nostr-bech32 string.

Args:
    prefix (str): prefix to be used by bech32 encoder.
    hexa (str): string to be encoded.
Returns:
    str: encoded string.
"""
    converted_bits = bech32.convertbits(bytes.fromhex(hexa), 8, 5)
    return bech32.bech32_encode(prefix, converted_bits, bech32.Encoding.BECH32)


def from_bech32(b32: str) -> str:
    """
Decode a nostr-bech32 string to hexadecimal string.

Args:
    b32 (str): nostr-bech32 encoded string.
Returns:
    str: decoded string.
Raises:
    Bech32DecodeError: if error occurs within bech32 module.
"""
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


class Bech32DecodeError(Exception):
    """Exception used for unsuccessful bech32 processing"""
    pass
