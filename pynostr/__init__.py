# -*- coding: utf-8 -*-

"""
This module provides nostr basic functionalities.
"""

import os
import re
import json
import pyaes
import base64
import hashlib
import binascii
import websockets
import cSecp256k1

from collections import namedtuple
from pynostr import bech32
from typing import Union


HEX64 = re.compile("^[0-9a-f]{64}$")

__path__.append(os.path.join(os.path.dirname(__file__), "nip"))

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
        out.write(
            json.dumps(list(sorted(contacts, key=lambda c: c[-1])), indent=2)
        )


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
    >>> e = event.Event.text_note("Hello nostr !")
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
Encode string to `bech32`.

Args:
    prefix (str): prefix to be used by bech32 encoder.
    hexa (str): string to be encoded.
Returns:
    str: `bech32` encoded string.
"""
    converted_bits = bech32.convertbits(bytes.fromhex(hexa), 8, 5)
    return bech32.bech32_encode(prefix, converted_bits, bech32.Encoding.BECH32)


def from_bech32(b32: str) -> str:
    """
Decode a `bech32` encoded string.

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
https://github.com/nostr-protocol/nips/blob/master/19.md).

Args:
    pubkey (str): public key as hex string
Returns:
    str: `nostr` encoded  public key
"""
    return to_bech32("npub", pubkey)


def bech32_prk(prvkey: str) -> str:
    """
Return a nostr private key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md).

Args:
    prvkey (str): private key as hex string
Returns:
    str: `nostr` encoded private key
"""
    return to_bech32("nsec", prvkey)


def bech32_nid(noteid: str) -> str:
    """
Return a nostr event id according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md).

Args:
    noteid (str): event id as hex string
Returns:
    str: `nostr` encoded event id
"""
    return to_bech32("note", noteid)


class Bech32DecodeError(Exception):
    """Exception used for unsuccessful bech32 processing."""
    pass


class Nip04EncryptionError(Exception):
    """Exception used for unsuccessful nip04 processing."""
    pass


class Base64ProcessingError(Exception):
    """Exception used for unsuccessful base64 processing."""
    pass


class PrvKey(cSecp256k1.Schnorr):
    """
`PrvKey` is a `secp256k1` private key used to issue `schnorr` signatures. It is
a subclass of python `int` with cryptographic attributes and methods.

Attributes:
    encpuk (property): secp256k1 encoded public key.
    pubkey (property): nostr encoded public key.
    npub (property): bech32 encoded nostr public key.
    nsec (property): bech32 encoded nostr private key.
Examples:
    Bellow basic uses of [PrvKey](#pynostr.PrvKey):

    ```python
    >>> k = pynostr.PrvKey("12-word secret phrase according to BIP-39")
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

    [PrvKey](#pynostr.PrvKey) can also be used to sign events like so:

    ```python
    >>> import pynostr
    >>> import asyncio
    >>> from pynostr import event
    >>> k = pynostr.PrvKey("12-word secret phrase according to BIP-39")
    >>> e = event.Event(kind=1, "Hello nostr !")
    >>> e.sign(k)
    >>> e.send_to("wss://relay.nostr.info")
    ['OK', '0459b[...]f2e99', True, '']
    ```

    [PrvKey](#pynostr.PrvKey) can also encrypt text for a specific public key
    destnation.

    ```python
    >>> import pynostr
    >>> k1 = pynostr.PrvKey("12-word secret phrase according to BIP-39")
    >>> k2 = pynostr.PrvKey("another 12-word secret phrase")
    >>> enc = k1.encrypt("simple message", k2.pubkey)
    >>> print(enc)
    'BQkp9Iy+eQGzK8vI9lUJjQ==?iv=89gjlOGyJVKML76nvQBo1g=='
    >>> k2.decrypt(enc, k1.pubkey)
    'simple message'
    ```

"""

    @property
    def encpuk(self) -> str:
        "`secp256k1` encoded public key."
        return cSecp256k1.Schnorr.puk(self).encode().decode("utf-8")

    @property
    def pubkey(self) -> str:
        "`schnorr` encoded public key."
        return cSecp256k1.Schnorr.puk(self).x.decode("utf-8")

    @property
    def npub(self) -> str:
        "`nostr` encoded public key."
        return bech32_puk(self.pubkey)

    @property
    def nsec(self) -> str:
        "`nostr` encoded private key."
        return bech32_prk("%064x" % self)

    @staticmethod
    def from_bech32(b32prk: str) -> object:
        "Create à [PrvKey](#pynostr.PrvKey) from `nostr` encoded private key"
        return PrvKey(int(from_bech32(b32prk), base=16))

    @staticmethod
    def load(pin: str) -> object:
        """
Load a [PrvKey](#pynostr.PrvKey) from file.

Arguments:
    pin (str): pin code used to decrypt private key and to determine filename.
"""
        pin = pin.encode("utf-8")
        fn = os.path.join(
            os.path.dirname(__file__), ".prvkey",
            "%s.key" % hashlib.sha256(pin).hexdigest()
        )
        if os.path.isfile(fn):
            with open(fn, "rb") as input:
                aes = pyaes.AESModeOfOperationCTR(hashlib.sha256(pin).digest())
                data = aes.decrypt(base64.b64decode(input.read()))
                return PrvKey(int(data.decode("utf-8"), 16))

    def dump(self, pin: str) -> None:
        """
Store a [PrvKey](#pynostr.PrvKey) into file.

Arguments:
    pin (str): pin code used to encrypt private key and to determine filename.
Returns:
    pynostr.PrvKey: private key
"""
        pin = pin.encode("utf-8")
        fn = os.path.join(
            os.path.dirname(__file__), ".prvkey",
            "%s.key" % hashlib.sha256(pin).hexdigest()
        )
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        aes = pyaes.AESModeOfOperationCTR(hashlib.sha256(pin).digest())
        data = base64.b64encode(aes.encrypt(("%064x" % self).encode("utf-8")))
        with open(fn, "wb") as output:
            output.write(data)

    def shared_secret(self, pubkey: str) -> str:
        """
Compute a shared secret with a specifc public key. This comes from public key
definition : `P = s x G`. Given two secrets `s1` and `s2` we can define the
public keys `P1 = s1 x G` and `P2 = s2 x G` giving
`P1 x (1/s1) = P2 x (1/s2) = G` and finally **`P1 x s2 = P2 x s1`**.

Arguments:
    pubkey (str): Public key to share common secret with. The public key owner
        is the targeted user to decrypt the message with its private key.
Returns:
    str: shared secret. It is the x abcsissa of curve point issued by
        [`PrvKey`](#pynostr.PrvKey)` x csecp256k1.PublicKey`
"""
        if pubkey.startswith("npub"):
            pubkey = "02" + from_bech32(pubkey)
        elif len(pubkey) == 64:
            pubkey = "02" + pubkey
        return (cSecp256k1.PublicKey.decode(pubkey) * self).x.decode("utf-8")

    def encrypt(self, msg: Union[str, bytes], pubkey: str) -> str:
        """
Encrypt a message to be read by the owner of a specific public key. Message and
initialization vector are base 64 encoded and joint using url query syntax with
`iv=` keyword (see [NIP-04](
            https://github.com/nostr-protocol/nips/blob/master/04.md
        ) specifcation).

Arguments:
    msg (str or bytes): message to encrypt.
    pubkey (str): schnorr normalized public key (ie public key x absissa) as
        hexadecimal string. The public key owner is the targeted user to
        decrypt the message with its private key.
Returns:
    str: encrypted text.
"""
        initialization_vector = os.urandom(16)
        cipher = _encrypt(
            msg, binascii.unhexlify(self.shared_secret(pubkey)),
            initialization_vector
        )
        cipher = base64.b64encode(cipher)
        initialization_vector = base64.b64encode(initialization_vector)
        return (cipher + b"?iv=" + initialization_vector).decode("utf-8")

    def decrypt(self, msg: str, pubkey: str) -> str:
        """
Decrypt a message created by the owner of a specific public key.

Arguments:
    msg (str or bytes): message to decrypt.
    pubkey (str): schnorr normalized public key (ie public key x absissa) as
        hexadecimal string. The public key owner is the issuer of the encrypted
        message.
Returns:
    str: decrypted text.
Raises:
    Nip04EncryptionError: if initialization vector can not be determined.
    Base64ProcessingError: if message is not correclty base-64 encoded.
"""
        try:
            cipher, iv = msg.split("?iv=")
        except ValueError:
            raise Nip04EncryptionError(
                "message is not nip04 compliant, can not determine "
                "initialization vector ('?iv=' probably missing)"
            )
        try:
            cipher = base64.b64decode(cipher, validate=True)
            iv = base64.b64decode(iv, validate=True)
        except binascii.Error:
            raise Base64ProcessingError(
                "message is not nip04 compliant, "
                "can not apply base 64 decoder"
            )
        decrypted = _decrytp(
            cipher, binascii.unhexlify(self.shared_secret(pubkey)), iv=iv
        )
        return decrypted.decode("utf-8")


def _encrypt(msg: Union[str, bytes], secret: bytes, iv: bytes) -> bytes:
    encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(secret, iv=iv))
    msg = msg.encode("utf-8") if isinstance(msg, str) else msg
    return encrypter.feed(msg) + encrypter.feed()


def _decrytp(cipher: Union[str, bytes], secret: bytes, iv: bytes) -> bytes:
    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(secret, iv=iv))
    cipher = cipher.encode("utf-8") if isinstance(cipher, str) else cipher
    return decrypter.feed(cipher) + decrypter.feed()


def _prvkey(prvkey: Union[str, PrvKey]):
    if isinstance(prvkey, PrvKey):
        return prvkey
    else:
        if prvkey.startswith("nsec"):
            prvkey = int(from_bech32(prvkey), base=16)
        elif prvkey and HEX64.match(prvkey):
            prvkey = int(prvkey, base=16)
        return PrvKey(prvkey)


def _pubkey(pubkey: Union[str, cSecp256k1.PublicKey]):
    if isinstance(pubkey, cSecp256k1.PublicKey):
        pubkey = pubkey.x.decode("utf-8")
    else:
        if pubkey.startswith("npub"):
            pubkey = from_bech32(pubkey)
        elif not HEX64.match(pubkey):
            pubkey = pubkey[2:]
        return pubkey
