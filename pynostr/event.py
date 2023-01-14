# -*- coding: utf-8 -*-
"""
[References](https://github.com/nostr-protocol/nips)
"""

import os
import re
import json
import time
import pyaes
import base64
import hashlib
import pynostr
import asyncio
import binascii
import cSecp256k1

from typing import Union, Tuple
from enum import IntEnum


HEX = re.compile("^[0-9a-f]*$")
HEX64 = pynostr.HEX64
HEX128 = re.compile("^[0-9a-f]{128}$")
EMAIL = re.compile(
    r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
)


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


class OrphanEvent(Exception):
    """Exception used when public key owner is missing"""


class Nip05FormatError(Exception):
    """Exception used when NIP 05 format is not correct"""


class EventType(IntEnum):
    # https://github.com/nostr-protocol/nips/blob/master/01.md
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMENDED_SERVER = 2
    # https://github.com/nostr-protocol/nips/blob/master/02.md
    # CONTACT_LIST = 3
    # https://github.com/nostr-protocol/nips/blob/master/04.md
    ENCRYPTED_MESSAGE = 4
    # https://github.com/nostr-protocol/nips/blob/master/09.md
    # EVENT_DELETE = 5
    # https://github.com/nostr-protocol/nips/blob/master/25.md
    # REACTION = 7
    # https://github.com/nostr-protocol/nips/blob/master/28.md
    # CHANNEL_CREATE = 40
    # CHANNEL_METADATA = 41
    # CHANNEL_MESSAGE = 42
    # CHANNEL_HIDE = 43
    # CHANNEL_MUTE = 44


# https://github.com/nostr-protocol/nips/blob/master/10.md#marked-e-tags-preferred
class TagList(list):

    @property
    def p(self) -> tuple:
        return self.find("p")

    @property
    def e(self) -> tuple:
        return self.find("e")

    @property
    def all(self) -> dict:
        result = {}
        for tag in self:
            tag_0 = tag[0]
            result[tag_0] = result.get(tag_0, ()) + (tag[1:], )
        return result

    def find(self, key: str) -> tuple:
        return tuple(tag for tag in self if tag[0] == key)

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
        return -1


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
    tags (pynostr.event.TagList): tag list.
    content (str): event content.
    sig (str): hexadecimal raw representation of schnorr signature computed
        over the event id.
"""

    @staticmethod
    def from_relay(data: str):
        return Event(json.loads(data[-1]))

    @staticmethod
    def set_metadata(
        name: str, about: str, picture: str,
        prvkey: Union[str, pynostr.PrvKey] = None
    ):
        """
Create and sign a `set metadata` event.

Arguments:
    name (str): nickname to be used by user.
    about (str): few words about user.
    picture (str): avatar url (IPFS, URL or base64 data).
    prvkey (str or pynostr.PrvKey): private key to sign the message. if not
        given, it will be asked on terminal.
Returns:
    event.Metadata: signed event instance.
"""
        return Metadata(
            kind=EventType.SET_METADATA,
            content=json.dumps(
                {"name": name, "about": about, "picture": picture},
                separators=(",", ":")
            )
        ).sign(prvkey)

    @staticmethod
    def text_note(content: str, prvkey: Union[str, pynostr.PrvKey] = None):
        """
Create and sign a `text note` event.

Arguments:
    content (str): the text note itself.
    prvkey (str or pynostr.PrvKey): private key to sign the message. if not
        given, it will be asked on terminal.
Returns:
    event.Event: signed event instance.
"""
        return Event(kind=EventType.TEXT_NOTE, content=content).sign(prvkey)

    @staticmethod
    def encrypted_message(
        content: str, pubkey: str, prvkey: Union[str, pynostr.PrvKey] = None
    ):
        """Create and sign an `encrypted message` event."""
        prvkey = pynostr._prvkey(prvkey)
        event = Event(
            kind=EventType.ENCRYPTED_MESSAGE,
            content=prvkey.encrypt(content, pubkey)
        )
        event.tags.add_pubkey(pubkey)
        return event.sign(prvkey)

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
        """
Initialize instance from python data. Only valid Event attributes will be set.

Arguments:
    cnf (dict): key-value pairs.
    **kw: arbitrary keyword arguments.
"""
        params = dict(cnf, **kw)
        if len(params):
            for key in [k for k in self.__dict__ if k in params]:
                if key == "tags":
                    value = TagList(params.get(key, []))
                else:
                    value = params.get(key, None)
                setattr(self, key, value)

    def serialize(self) -> str:
        """
Serialize instance according to [NIP-01](
    https://github.com/nostr-protocol/nips/blob/master/01.md
)

Returns:
    str: serialization of event (UTF-8 JSON-serialized string with no white
        space or line breaks).
"""
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
        """
Compute id attribute according to [NIP-01](
    https://github.com/nostr-protocol/nips/blob/master/01.md
).
"""
        self.id = hashlib.sha256(self.serialize()).hexdigest()

    def verify(self) -> bool:
        """
Check integrity of event and signature.

Returns:
    bool: `True` if event is genuine, `False` other else.
Raises:
    IntegrityError: if id does not match with the event. This is to prevent
        issue [#59](https://github.com/fiatjaf/nostr-tools/issues/59).
"""
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

    def sign(self, prvkey: Union[str, pynostr.PrvKey] = None) -> object:
        """
Sign event.

Arguments:
    prvkey (str or pynostr.PrvKey): private key to sign the message. If not
        given, it will be asked on terminal.
Returns:
    event.Event: signed event instance.
"""
        prvkey = pynostr._prvkey(prvkey)
        self.pubkey = prvkey.pubkey
        serial = self.serialize()
        self.id = hashlib.sha256(serial).hexdigest()
        self.sig = prvkey.sign(serial).raw().decode("utf-8")

        return self

    def set_pow_tag(self, difficulty: int = 0) -> list:
        """
Compute proof of work tag according to [NIP-13](
https://github.com/nostr-protocol/nips/blob/master/13.md).

Arguments:
    difficulty (int): level of difficulty to compute the nonce.
"""
        if self.pubkey:
            # compute 256 bit mask associated to difficulty
            mask = int("1" * difficulty, base=2) << (256 - difficulty)
            # compute seiral with void nonce tag
            serial = json.dumps(
                [
                    0, self.pubkey, self.created_at, self.kind,
                    self.tags + [["nonce", "%s", f"{difficulty}"], ],
                    self.content
                ], separators=(",", ":"), ensure_ascii=False
            )
            # local shortcut to speed up while loop
            enc = str.encode
            sha256 = hashlib.sha256
            nonce = 0
            while int(sha256(enc(serial % nonce)).hexdigest(), base=16) & mask:
                nonce += 1

            self.tags.append(["nonce", "%s" % nonce, "%s" % (difficulty)])
            self.identify()
        else:
            raise OrphanEvent("No owner identified, missing public key")

    def encrypt(
        self, prvkey: Union[str, pynostr.PrvKey],
        *pubkeys: Union[Tuple[str], Tuple[pynostr.cSecp256k1.PublicKey]],
    ):
        """
Encrypt event content, tags and kind according to NIP-04 and NIP-48.

Arguments:
    prvkey (str or pynostr.PrvKey): issuer private key. It computes shared
        secret(s) with public key(s) and also set the event public key.
    *pubkeys: variable length argument of public key. All public keys are added
        to event tags.
Returns:
    str: the event content.
Raises:
    Exception: if no pubkey is given.
"""
        prvkey = pynostr._prvkey(prvkey)
        pubkeys = [pynostr._pubkey(puk) for puk in pubkeys]

        if len(pubkeys) > 1:
            # NIP-48
            # if multiple pubkey are given for encryption, use NIP-48
            # specification to encrypt event.
            secret = hashlib.sha256(self.content.encode("utf-8")).digest()
            for pubkey in pubkeys:
                aes = pyaes.AESModeOfOperationCTR(
                    binascii.unhexlify(prvkey.shared_secret(pubkey))
                )
                self.tags.add_pubkey(
                    pubkey, "",
                    base64.b64encode(aes.encrypt(secret)).decode("utf-8")
                )
        elif len(pubkeys) == 1:
            # NIP-04
            pubkey = pubkeys[0]
            secret = binascii.unhexlify(prvkey.shared_secret(pubkey))
            if pubkey not in (t[1]for t in self.tags.p):
                self.tags.add_pubkey(pubkey)
        else:
            raise Exception(
                "At least one public key is needed to encrypt event"
            )

        iv = os.urandom(16)
        cipher = base64.b64encode(pynostr._encrypt(self.content, secret, iv))

        self.pubkey = prvkey.pubkey
        self.kind = EventType.ENCRYPTED_MESSAGE
        self.content = (
            cipher + b"?iv=" + base64.b64encode(iv)
        ).decode("utf-8")
        return self.content

    def decrypt(self, prvkey: Union[str, pynostr.PrvKey]):
        prvkey = pynostr._prvkey(prvkey)
        pubkey = prvkey.pubkey

        tag = [t for t in self.tags if t[1] == pubkey]
        if len(tag) == 0:
            raise EmptyTagException(f"{pubkey} not mentioned in event tags")

        try:
            secret = base64.b64decode(
                tag[0][3].encode("utf-8"), validate=True
            )
        except (binascii.Error, IndexError):
            # NIP-04
            secret = binascii.unhexlify(prvkey.shared_secret(self.pubkey))
        else:
            # NIP-48
            aes = pyaes.AESModeOfOperationCTR(
                binascii.unhexlify(prvkey.shared_secret(self.pubkey))
            )
            secret = aes.decrypt(secret)

        try:
            cipher, iv = self.content.split("?iv=")
        except ValueError:
            raise pynostr.Nip04EncryptionError(
                "message is not nip04 complient, can not determine "
                "initialization vector ('?iv=' probably missing)"
            )
        try:
            cipher = base64.b64decode(cipher)
            iv = base64.b64decode(iv)
        except Exception:
            raise pynostr.Base64ProcessingError(
                "message is not nip04 complient, "
                "can not apply base 64 decoder"
            )

        decrypted = pynostr._decrytp(cipher, secret, iv=iv)
        return decrypted.decode("utf-8")

    def send_to(self, url: str):
        return asyncio.run(pynostr.send_event(self.__dict__, url))


class Metadata(Event):
    """
Metadata specific Event subclass. It defines metadata fields as property with
getter and setter. Values are extracted from content string or injected in it.

Examples:
    ```python
    >>> e = event.Event.set_metadata(
    ...     name="toons", about="None", picture="None", prvkey=k
    ... )
    >>> print(e.content)
    {'name': 'toons', 'about': 'None', 'picture': 'None'}
    >>> e.about = ""
    >>> prnt(e.content)
    {'name': 'toons', 'about': '', 'picture': 'None'}
    ```
"""

    @property
    def name(self) -> str:
        return json.loads(self.content).get("name", "")

    @name.setter
    def name(self, value: str):
        self.content = json.dumps(dict(json.loads(self.content), name=value))

    @property
    def about(self) -> str:
        return json.loads(self.content).get("about", "")

    @about.setter
    def about(self, value: str):
        self.content = json.dumps(dict(json.loads(self.content), about=value))

    @property
    def picture(self) -> str:
        return json.loads(self.content).get("picture", "")

    @picture.setter
    def picture(self, value: str):
        self.content = json.dumps(
            dict(json.loads(self.content), picture=value)
        )

    @property
    def nip05(self) -> str:
        return json.loads(self.content).get("nip05", None)

    @nip05.setter
    def nip05(self, value: str):
        if EMAIL.match(value):
            self.content = json.dumps(
                dict(json.loads(self.content), nip05=value)
            )
        else:
            raise Nip05FormatError(
                f"{value} does not match NIP 05 specification"
            )

    def add_value(self, key: str, value: str):
        self.content = json.dumps(
            dict(json.loads(self.content), **{key: value})
        )

    def add_values(self, cnf: dict = {}, **kw):
        self.content = json.dumps(
            dict(json.loads(self.content), **dict(cnf, **kw))
        )

    def get(self, fieldname: str) -> str:
        return json.loads(self.content).get(fieldname, None)
