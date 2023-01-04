# -*- coding: utf-8 -*-

"""
This module provides nostr basic functionalities.
"""

import os
import json
import websockets
import cSecp256k1

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
    *contacts: variable length of [contact](#pynostr.Contact)
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
Examples:
    Here is a snippet of python code to send a text note to a specific nostr
    relay:

    ```python
    >>> import pynostr
    >>> import asyncio
    >>> from pynostr import event
    >>> e = event.Event.text_note("Hello nostr !").sign()
    Type or paste your passphrase >
    >>> asyncio.run(pynostr.send_event(e.__dict__, "wss://relay.nostr.info"))
    ['OK', '2781d[...]d28c9', True, '']
    ```
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


class Keyring(cSecp256k1.Schnorr):
    """
`Keyring` class is used to manage secp256k1 keys. It is a subclass of python
`int` with cryptographic attributes and methods.

Attributes:
    encpuk (property): secp256k1 encoded public key.
    pubkey (property): nostr encoded public key.
    npub (property): bech32 encoded nostr public key.
    nsec (property): bech32 encoded nostr private key.
Examples:
    Bellow basic uses of [Keyring](#pynostr.Keyring):

    ```python
    >>> k = pynostr.Keyring("12-word secret phrase according to BIP-39")
    >>> k.encpuk
    '02a549420d3f3a64e59855e8c640f7c611ca567b9862fa4d10aba1c676aa7036c5'
    >>> k.pubkey
    'a549420d3f3a64e59855e8c640f7c611ca567b9862fa4d10aba1c676aa7036c5'
    >>> k.npub
    'npub154y5yrfl8fjwtxz4arrypa7xz899v7ucvtay6y9t58r8d2nsxmzsvad8yf'
    >>> k.nsec
    'nsec1mvqqm229tvkd4j395g76l2deumcwachl6lup4xyp0k76gyw6ztdsrqdvvu'
    >>> sig = k.sign("simple message").raw()
    >>> k.verify("simple message", sig)
    True
    >>> k.verify("other message", sig)
    False
    ```

    [Keyring](#pynostr.Keyring) can also be used to sign events like so:

    ```python
    >>> import pynostr
    >>> import asyncio
    >>> from pynostr import event
    >>> k = pynostr.Keyring("12-word secret phrase according to BIP-39")
    >>> e = event.Event(kind=1, "Hello nostr !")
    >>> e.sign(k)
    >>> e.send_to("wss://relay.nostr.info")
    ['OK', '0459b[...]f2e99', True, '']
    ```

"""

    @property
    def encpuk(self):
        return cSecp256k1.Schnorr.puk(self).encode().decode("utf-8")

    @property
    def pubkey(self):
        return cSecp256k1.Schnorr.puk(self).x.decode("utf-8")

    @property
    def npub(self):
        return bech32_puk(self.pubkey)

    @property
    def nsec(self):
        return bech32_prk("%064x" % self)

    @staticmethod
    def from_bech32(b32prk: str) -> str:
        return cSecp256k1.Schnorr(int(from_bech32(b32prk), base=16))
