<a id="pynostr"></a>

# pynostr

This module provides nostr basic functionalities.

<a id="pynostr.Contact"></a>

#### Contact

Contact is defined by a public key, a relay and a petname. It is implemented
as a `namedtuple` with `pubkey`, `relay` and `petname` fieldnames.
```python
>>> import pynostr
>>> contac = Contact(
...    pubkey=
...      "9aa650df414cc71b37176412aecba987727b6f1b8cd550f40e9ca10b7af5a239",
...    relay="wss://relay.nostr.info",
...    petname="Toon's"
... )
>>> print(contact)
Contact(pubkey='9aa65[...]5a239', relay='wss:/[...].info', petname="Toon's")
```

<a id="pynostr.dump_contact"></a>

#### dump\_contact

```python
def dump_contact(name: str, *contacts) -> None
```

Store a list of [contact](#pynostr.Contact) as json format. Files are stored in
`<pynostr.__path__[0]>/.contact` folder. Folder `.contact` is created if
needed.

**Arguments**:

- `name` _str_ - filename to be used.
- `*contacts` - variable length of [contact](#pynostr.Contact)

<a id="pynostr.load_contact"></a>

#### load\_contact

```python
def load_contact(name: str) -> list
```

Load a list of [contact](#pynostr.Contact) from a file stored in
`<pynostr.__path__[0]>/.contact` folder. Return an empty list if file or
`.contact` folder do not exist.

**Arguments**:

- `name` _str_ - filename to be used.

**Returns**:

- `list` - list of [contact](#pynostr.Contact).

<a id="pynostr.send_event"></a>

#### send\_event

```python
async def send_event(event: dict, uri: str) -> list
```

Push single event to a single relay and return responses.

**Arguments**:

- `event` _dict_ - the event given as a python dict.
- `uri` _str_ - relay uri.

**Returns**:

- `list` - relay response as python list.

**Examples**:

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

<a id="pynostr.to_bech32"></a>

#### to\_bech32

```python
def to_bech32(prefix: str, hexa: str) -> str
```

Encode string to `bech32`.

**Arguments**:

- `prefix` _str_ - prefix to be used by bech32 encoder.
- `hexa` _str_ - string to be encoded.

**Returns**:

- `str` - `bech32` encoded string.

<a id="pynostr.from_bech32"></a>

#### from\_bech32

```python
def from_bech32(b32: str) -> str
```

Decode a `bech32` encoded string.

**Arguments**:

- `b32` _str_ - nostr-bech32 encoded string.

**Returns**:

- `str` - decoded string.

**Raises**:

- `Bech32DecodeError` - if error occurs within bech32 module.

<a id="pynostr.bech32_puk"></a>

#### bech32\_puk

```python
def bech32_puk(pubkey: str) -> str
```

Return a nostr public key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md).

**Arguments**:

- `pubkey` _str_ - public key as hex string

**Returns**:

- `str` - `nostr` encoded  public key

<a id="pynostr.bech32_prk"></a>

#### bech32\_prk

```python
def bech32_prk(prvkey: str) -> str
```

Return a nostr private key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md).

**Arguments**:

- `prvkey` _str_ - private key as hex string

**Returns**:

- `str` - `nostr` encoded private key

<a id="pynostr.bech32_nid"></a>

#### bech32\_nid

```python
def bech32_nid(noteid: str) -> str
```

Return a nostr event id according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md).

**Arguments**:

- `noteid` _str_ - event id as hex string

**Returns**:

- `str` - `nostr` encoded event id

<a id="pynostr.Bech32DecodeError"></a>

## Bech32DecodeError Objects

```python
class Bech32DecodeError(Exception)
```

Exception used for unsuccessful bech32 processing.

<a id="pynostr.Nip04EncryptionError"></a>

## Nip04EncryptionError Objects

```python
class Nip04EncryptionError(Exception)
```

Exception used for unsuccessful nip04 processing.

<a id="pynostr.Base64ProcessingError"></a>

## Base64ProcessingError Objects

```python
class Base64ProcessingError(Exception)
```

Exception used for unsuccessful base64 processing.

<a id="pynostr.PrvKey"></a>

## PrvKey Objects

```python
class PrvKey(cSecp256k1.Schnorr)
```

`PrvKey` is a `secp256k1` private key used to issue `schnorr` signatures. It is
a subclass of python `int` with cryptographic attributes and methods.

**Attributes**:

- `encpuk` _property_ - secp256k1 encoded public key.
- `pubkey` _property_ - nostr encoded public key.
- `npub` _property_ - bech32 encoded nostr public key.
- `nsec` _property_ - bech32 encoded nostr private key.

**Examples**:

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

<a id="pynostr.PrvKey.encpuk"></a>

#### encpuk

```python
@property
def encpuk() -> str
```

`secp256k1` encoded public key.

<a id="pynostr.PrvKey.pubkey"></a>

#### pubkey

```python
@property
def pubkey() -> str
```

`schnorr` encoded public key.

<a id="pynostr.PrvKey.npub"></a>

#### npub

```python
@property
def npub() -> str
```

`nostr` encoded public key.

<a id="pynostr.PrvKey.nsec"></a>

#### nsec

```python
@property
def nsec() -> str
```

`nostr` encoded private key.

<a id="pynostr.PrvKey.from_bech32"></a>

#### from\_bech32

```python
@staticmethod
def from_bech32(b32prk: str) -> object
```

Create à [PrvKey](#pynostr.PrvKey) from `nostr` encoded private key

<a id="pynostr.PrvKey.load"></a>

#### load

```python
@staticmethod
def load(pin: str) -> object
```

Load a [PrvKey](#pynostr.PrvKey) from file.

**Arguments**:

- `pin` _str_ - pin code used to decrypt private key and to determine filename.

<a id="pynostr.PrvKey.dump"></a>

#### dump

```python
def dump(pin: str) -> None
```

Store a [PrvKey](#pynostr.PrvKey) into file.

**Arguments**:

- `pin` _str_ - pin code used to encrypt private key and to determine filename.

**Returns**:

- `pynostr.PrvKey` - private key

<a id="pynostr.PrvKey.shared_secret"></a>

#### shared\_secret

```python
def shared_secret(pubkey: str) -> str
```

Compute a shared secret with a specifc public key. This comes from public key
definition : `P = s x G`. Given two secrets `s1` and `s2` we can define the
public keys `P1 = s1 x G` and `P2 = s2 x G` giving
`P1 x (1/s1) = P2 x (1/s2) = G` and finally **`P1 x s2 = P2 x s1`**.

**Arguments**:

- `pubkey` _str_ - Public key to share common secret with. The public key owner
  is the targeted user to decrypt the message with its private key.

**Returns**:

- `str` - shared secret. It is the x abcsissa of curve point issued by
  [`PrvKey`](#pynostr.PrvKey)` x csecp256k1.PublicKey`

<a id="pynostr.PrvKey.encrypt"></a>

#### encrypt

```python
def encrypt(msg: Union[str, bytes], pubkey: str) -> str
```

Encrypt a message to be read by the owner of a specific public key. Message and
initialization vector are base 64 encoded and joint using url query syntax with
`iv=` keyword (see [NIP-04](
https://github.com/nostr-protocol/nips/blob/master/04.md
) specifcation).

**Arguments**:

- `msg` _str or bytes_ - message to encrypt.
- `pubkey` _str_ - schnorr normalized public key (ie public key x absissa) as
  hexadecimal string. The public key owner is the targeted user to
  decrypt the message with its private key.

**Returns**:

- `str` - encrypted text.

<a id="pynostr.PrvKey.decrypt"></a>

#### decrypt

```python
def decrypt(msg: str, pubkey: str) -> str
```

Decrypt a message created by the owner of a specific public key.

**Arguments**:

- `msg` _str or bytes_ - message to decrypt.
- `pubkey` _str_ - schnorr normalized public key (ie public key x absissa) as
  hexadecimal string. The public key owner is the issuer of the encrypted
  message.

**Returns**:

- `str` - decrypted text.

**Raises**:

- `Nip04EncryptionError` - if initialization vector can not be determined.
- `Base64ProcessingError` - if message is not correclty base 64 encoded.

