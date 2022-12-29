# -*- coding: utf-8 -*-
"""
[References](https://github.com/nostr-protocol/nips)
"""

import re
import json
import time
import hashlib
import pynostr
import asyncio
import cSecp256k1

from enum import IntEnum


HEX = re.compile("^[0-9a-f]*$")
HEX64 = re.compile("^[0-9a-f]{64}$")
HEX128 = re.compile("^[0-9a-f]{128}$")


class EmptyTagException(Exception):
    """Exception used when at least one tag is empty"""


class EmptyEventException(Exception):
    """Exception used if one of required field is None"""


class InvalidHexString(Exception):
    """Exception used for hexadecimal string compliancy"""


class IntegrityError(Exception):
    """Exception used on event id mismatch"""


class GenuinityError(Exception):
    """Exception used on signature mismatch"""


class EventType(IntEnum):
    # https://github.com/nostr-protocol/nips/blob/master/01.md
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMENDED_SERVER = 2
    # # https://github.com/nostr-protocol/nips/blob/master/02.md
    # CONTACT_LIST = 3
    # # https://github.com/nostr-protocol/nips/blob/master/04.md
    # ENCRYPT_MESSAGE = 4
    # # https://github.com/nostr-protocol/nips/blob/master/09.md
    # EVENT_DELETE = 5
    # # https://github.com/nostr-protocol/nips/blob/master/25.md
    # REACTION = 7
    # # https://github.com/nostr-protocol/nips/blob/master/28.md
    # CHANNEL_CREATE = 40
    # CHANNEL_METADATA = 41
    # CHANNEL_MESSAGE = 42
    # CHANNEL_HIDE = 43
    # CHANNEL_MUTE = 44


# https://github.com/nostr-protocol/nips/blob/master/10.md#marked-e-tags-preferred
class TagList(list):

    @property
    def p(self) -> list:
        return tuple(tag for tag in self if tag[0] == "p")

    @property
    def e(self) -> list:
        return tuple(tag for tag in self if tag[0] == "e")

    @property
    def all(self) -> dict:
        result = {}
        for tag in self:
            tag_0 = tag[0]
            result[tag_0] = result.get(tag_0, ()) + (tag[1:], )
        return result

    def add_tag(self, key: str, *values) -> None:
        self.append([key] + ["%s" % v for v in values])

    def add_event(
        self, event_id: str, url: str = "", marker: str = None
    ) -> None:
        if not HEX64.match(event_id):
            raise InvalidHexString(
                "event id '%s' should be lenght-64" % event_id
            )
        data = ["e", event_id, url]
        if marker in ["root", "reply"]:
            data.append(marker)
        self.append(data)

    def add_pubkey(
        self, pubkey: str, url: str = "", petname: str = None
    ) -> None:
        if not HEX64.match(pubkey):
            raise InvalidHexString(
                "public key '%s' should be lenght-64" % pubkey
            )
        data = ["p", pubkey, url]
        if petname is not None:
            data.append(petname)
        self.append(data)

    def reference(self, puk_or_evnt: str) -> int:
        for tag in self:
            if tag[1] == puk_or_evnt:
                return self.index(tag)


# https://github.com/nostr-protocol/nips/blob/master/01.md
class Event:
    """
Nostr event object implementation accordnig to [NIP-01](
    https://github.com/nostr-protocol/nips/blob/master/01.md
).

Arguments:
    cnf (dict): key-value pairs.
    **kw: arbitrary keyword arguments.
Attributes:
    id (str): hexadecimal string that is computed over the UTF-8-serialized
        string (with no white space or line breaks).
    pubkey (str): owner public key that is the hexadecimal expression of the
        secp256k1-point bscissa (x).
    created_at (int): unix timestamp.
    kind (int): event type.
    tags (list): tag list.
    content (str): event content.
    sig (str): hexadecimal raw representation of schnorr signature computed
        over the event id.
"""

    @staticmethod
    def set_metadata(name: str, about: str, picture: str, prvkey: str = None):
        e = Event(
            kind=EventType.SET_METADATA,
            content={"name": name, "about": about, "picture": picture}
        )
        if prvkey is not None:
            e.sign(prvkey)
        return e

    @staticmethod
    def text_note(content: str, prvkey: str = None):
        e = Event(kind=EventType.TEXT_NOTE, content=content)
        if prvkey is not None:
            e.sign(prvkey)
        return e

    def __init__(self, cnf: dict = {}, **kw) -> None:
        self.id = None
        self.pubkey = None
        self.created_at = int(time.time())
        self.kind = None
        self.tags = TagList()
        self.content = None
        self.sig = None

        self.load(cnf, **kw)

    def load(self, cnf: dict = {}, **kw) -> None:
        params = dict(cnf, **kw)
        if len(params):
            for key in [k for k in self.__dict__ if k in params]:
                if key == "tags":
                    value = TagList(params.get(key, []))
                else:
                    value = params.get(key, None)
                setattr(self, key, value)

    def serialize(self) -> str:
        missings = [
            k for k, v in self.__dict__.items()
            if v is None and k not in ["id", "sig"]
        ]
        if missings:
            raise EmptyEventException(
                "Empty field in Event class\n"
                "  missing %s" % (", ".join(missings))
            )

        if any([len(t) == 0 for t in self.tags]):
            raise EmptyTagException()

        return json.dumps(
            [
                0, self.pubkey, self.created_at, self.kind, self.tags,
                self.content
            ],
            separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    def identify(self) -> None:
        self.id = hashlib.sha256(self.serialize()).hexdigest()

    def verify(self) -> bool:
        # https://github.com/fiatjaf/nostr-tools/issues/59
        # have to check integrity and genuinity of event
        if self.id != hashlib.sha256(self.serialize()).hexdigest():
            raise IntegrityError()
        if self.sig is not None:
            if bool(
                cSecp256k1._schnorr.verify(
                    self.id.encode("utf-8"),
                    self.pubkey.encode("utf-8"),
                    self.sig[:64].encode("utf-8"),
                    self.sig[64:].encode("utf-8")
                )
            ):
                return True
        return False

    def sign(self, prvkey=None) -> object:
        if isinstance(prvkey, pynostr.Keyring):
            keyring = prvkey
        else:
            if prvkey and HEX64.match(prvkey):
                prvkey = int(prvkey, base=16)
            keyring = pynostr.Keyring(prvkey)

        self.pubkey = keyring.pubkey
        serial = self.serialize()
        self.id = hashlib.sha256(serial).hexdigest()
        self.sig = keyring.sign(serial).raw().decode("utf-8")

        return self

    # https://github.com/nostr-protocol/nips/blob/master/13.md
    def set_pow_tag(self, difficulty: int = 0) -> list:
        # 4 bits per byte so for one 0 divide by 4
        leading_0 = "0" * (difficulty // 4)
        n_0 = len(leading_0)
        # compute seiral with void nonce tag
        serial = json.dumps(
            [
                0, self.pubkey, self.created_at, self.kind,
                self.tags + [["nonce", "%s", "%s" % (n_0 * 4)], ],
                self.content
            ], separators=(",", ":"), ensure_ascii=False
        )
        # local shortcut to speed up while loop
        enc = str.encode
        sha256 = hashlib.sha256
        nonce = 0
        while not sha256(enc(serial % nonce)).hexdigest()[:n_0] == leading_0:
            nonce += 1

        self.tags.append(["nonce", "%s" % nonce, "%s" % (n_0 * 4)])

    def send_to(self, url: str):
        return asyncio.run(pynostr.send_event(self.__dict__, url))
