# -*- coding: utf-8 -*-
"""
`pynostr` aims to provide a simple interface to interact with nostr
environment.
"""

import os
import json

from collections import namedtuple
from pynostr import bech32

Contact = namedtuple('Contact', 'pubkey relay petname')


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


def pubkey(pubkey: str) -> str:
    """
Return a nostr public key according to [NIPS-19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    pubkey (str): public key as hex string

Returns:
    str: nostr public key
"""
    converted_bits = bech32.convertbits(bytes.fromhex(pubkey), 8, 5)
    return bech32.bech32_encode("npub", converted_bits, bech32.Encoding.BECH32)


def prvkey(prvkey: str) -> str:
    """
Return a nostr private key according to [NIPS-19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    prvkey (str): private key as hex string

Returns:
    str: nostr private key
"""
    converted_bits = bech32.convertbits(bytes.fromhex(prvkey), 8, 5)
    return bech32.bech32_encode("nsec", converted_bits, bech32.Encoding.BECH32)


def noteid(noteid: str) -> str:
    """
Return a nostr event id according to [NIPS-19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

Args:
    noteid (str): event id as hex string

Returns:
    str: nostr event id
"""
    converted_bits = bech32.convertbits(bytes.fromhex(noteid), 8, 5)
    return bech32.bech32_encode("note", converted_bits, bech32.Encoding.BECH32)
