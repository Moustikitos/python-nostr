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
  >>> e = event.Event.text_note("Hello nostr !").sign()
  Type or paste your passphrase >
  >>> asyncio.run(pynostr.send_event(e.__dict__, "wss://relay.nostr.info"))
  ['OK', '2781d[...]d28c9', True, '']
  ```

<a id="pynostr.to_bech32"></a>

#### to\_bech32

```python
def to_bech32(prefix: str, hexa: str) -> str
```

Encode string to a prefixed nostr-bech32 string.

**Arguments**:

- `prefix` _str_ - prefix to be used by bech32 encoder.
- `hexa` _str_ - string to be encoded.

**Returns**:

- `str` - encoded string.

<a id="pynostr.from_bech32"></a>

#### from\_bech32

```python
def from_bech32(b32: str) -> str
```

Decode a nostr-bech32 string to hexadecimal string.

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
https://github.com/nostr-protocol/nips/blob/master/19.md)

**Arguments**:

- `pubkey` _str_ - public key as hex string

**Returns**:

- `str` - nostr public key

<a id="pynostr.bech32_prk"></a>

#### bech32\_prk

```python
def bech32_prk(prvkey: str) -> str
```

Return a nostr private key according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

**Arguments**:

- `prvkey` _str_ - private key as hex string

**Returns**:

- `str` - nostr private key

<a id="pynostr.bech32_nid"></a>

#### bech32\_nid

```python
def bech32_nid(noteid: str) -> str
```

Return a nostr event id according to [NIP 19](
https://github.com/nostr-protocol/nips/blob/master/19.md)

**Arguments**:

- `noteid` _str_ - event id as hex string

**Returns**:

- `str` - nostr event id

<a id="pynostr.Bech32DecodeError"></a>

## Bech32DecodeError Objects

```python
class Bech32DecodeError(Exception)
```

Exception used for unsuccessful bech32 processing

<a id="pynostr.PrvKey"></a>

## PrvKey Objects

```python
class PrvKey(cSecp256k1.Schnorr)
```

`PrvKey` class is used to manage secp256k1 keys. It is a subclass of python
`int` with cryptographic attributes and methods.

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

