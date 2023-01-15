<a id="pynostr.event"></a>

# pynostr.event

[References](https://github.com/nostr-protocol/nips)

<a id="pynostr.event.EmptyTagException"></a>

## EmptyTagException Objects

```python
class EmptyTagException(Exception)
```

Exception used when at least one tag is empty

<a id="pynostr.event.EmptyEventException"></a>

## EmptyEventException Objects

```python
class EmptyEventException(Exception)
```

Exception used if one of required field is None

<a id="pynostr.event.InvalidHexString"></a>

## InvalidHexString Objects

```python
class InvalidHexString(Exception)
```

Exception used for hexadecimal string compliancy

<a id="pynostr.event.IntegrityError"></a>

## IntegrityError Objects

```python
class IntegrityError(Exception)
```

Exception used on event id mismatch

<a id="pynostr.event.GenuinityError"></a>

## GenuinityError Objects

```python
class GenuinityError(Exception)
```

Exception used on signature mismatch

<a id="pynostr.event.OrphanEvent"></a>

## OrphanEvent Objects

```python
class OrphanEvent(Exception)
```

Exception used when public key owner is missing

<a id="pynostr.event.Nip05FormatError"></a>

## Nip05FormatError Objects

```python
class Nip05FormatError(Exception)
```

Exception used when NIP 05 format is not correct

<a id="pynostr.event.Event"></a>

## Event Objects

```python
class Event()
```

Nostr event object implementation accordnig to [NIP-01](
https://github.com/nostr-protocol/nips/blob/master/01.md
).

**Arguments**:

- `cnf` _dict_ - key-value pairs.
- `**kw` - arbitrary keyword arguments.

**Attributes**:

- `id` _str_ - hexadecimal string that is computed over the UTF-8-serialized
  string (with no white space or line breaks).
- `pubkey` _str_ - owner public key that is the hexadecimal expression of the
  secp256k1-point bscissa (x).
- `created_at` _int_ - unix timestamp.
- `kind` _int_ - event type.
- `tags` _pynostr.event.TagList_ - tag list.
- `content` _str_ - event content.
- `sig` _str_ - hexadecimal raw representation of schnorr signature computed
  over the event id.

<a id="pynostr.event.Event.set_metadata"></a>

#### set\_metadata

```python
@staticmethod
def set_metadata(name: str,
                 about: str,
                 picture: str,
                 prvkey: Union[str, pynostr.PrvKey] = None)
```

Create and sign a `set metadata` event.

**Arguments**:

- `name` _str_ - nickname to be used by user.
- `about` _str_ - few words about user.
- `picture` _str_ - avatar url (IPFS, URL or base64 data).
- `prvkey` _str or pynostr.PrvKey_ - private key to sign the message. if not
  given, it will be asked on terminal.

**Returns**:

- `event.Metadata` - signed event instance.

<a id="pynostr.event.Event.text_note"></a>

#### text\_note

```python
@staticmethod
def text_note(content: str, prvkey: Union[str, pynostr.PrvKey] = None)
```

Create and sign a `text note` event.

**Arguments**:

- `content` _str_ - the text note itself.
- `prvkey` _str or pynostr.PrvKey_ - private key to sign the message. if not
  given, it will be asked on terminal.

**Returns**:

- `event.Event` - signed event instance.

<a id="pynostr.event.Event.encrypted_message"></a>

#### encrypted\_message

```python
@staticmethod
def encrypted_message(content: str,
                      pubkey: str,
                      prvkey: Union[str, pynostr.PrvKey] = None)
```

Create and sign an `encrypted message` event.

<a id="pynostr.event.Event.load"></a>

#### load

```python
def load(cnf: dict = {}, **kw) -> None
```

Initialize instance from python data. Only valid Event attributes will be set.

**Arguments**:

- `cnf` _dict_ - key-value pairs.
- `**kw` - arbitrary keyword arguments.

<a id="pynostr.event.Event.serialize"></a>

#### serialize

```python
def serialize() -> str
```

Serialize instance according to [NIP-01](
https://github.com/nostr-protocol/nips/blob/master/01.md
)

**Returns**:

- `str` - serialization of event (UTF-8 JSON-serialized string with no white
  space or line breaks).

<a id="pynostr.event.Event.identify"></a>

#### identify

```python
def identify() -> None
```

Compute id attribute according to [NIP-01](
    https://github.com/nostr-protocol/nips/blob/master/01.md
).

<a id="pynostr.event.Event.verify"></a>

#### verify

```python
def verify() -> bool
```

Check integrity of event and signature.

**Returns**:

- `bool` - `True` if event is genuine, `False` other else.

**Raises**:

- `IntegrityError` - if id does not match with the event. This is to prevent
  issue [`59`](https://github.com/fiatjaf/nostr-tools/issues/59).

<a id="pynostr.event.Event.sign"></a>

#### sign

```python
def sign(prvkey: Union[str, pynostr.PrvKey] = None) -> object
```

Sign event.

**Arguments**:

- `prvkey` _str or pynostr.PrvKey_ - private key to sign the message. If not
  given, it will be asked on terminal.

**Returns**:

- `event.Event` - signed event instance.

<a id="pynostr.event.Event.set_pow_tag"></a>

#### set\_pow\_tag

```python
def set_pow_tag(difficulty: int = 0) -> list
```

Compute proof of work tag according to [NIP-13](
https://github.com/nostr-protocol/nips/blob/master/13.md).

**Arguments**:

- `difficulty` _int_ - level of difficulty to compute the nonce.

<a id="pynostr.event.Event.encrypt"></a>

#### encrypt

```python
def encrypt(
        prvkey: Union[str, pynostr.PrvKey],
        *pubkeys: Union[Tuple[str],
                        Tuple[pynostr.cSecp256k1.PublicKey]]) -> str
```

Encrypt event content according to NIP-04 and NIP-48. This method also sets
`tags`,  `kind` and `pubkey` attributes.

**Arguments**:

- `prvkey` _str or pynostr.PrvKey_ - issuer private key.
- `*pubkeys` - variable length argument of public key.

**Returns**:

- `str` - the event content.

**Raises**:

- `Exception` - if no pubkey is given.

<a id="pynostr.event.Event.decrypt"></a>

#### decrypt

```python
def decrypt(prvkey: Union[str, pynostr.PrvKey]) -> str
```

Decrypt event content according to NIP-04 and NIP-48.

**Arguments**:

- `prvkey` _str or pynostr.PrvKey_ - receiver private key.

**Returns**:

- `str` - decrypted message.

**Raises**:

- `EmptyTagException` - if public key is not identified as a receiver one in
  event tag list
- `Nip04EncryptionError` - if initialization vector can not be determined.
- `Base64ProcessingError` - if message is not correclty base-64 encoded.

<a id="pynostr.event.Metadata"></a>

## Metadata Objects

```python
class Metadata(Event)
```

Metadata specific Event subclass. It defines metadata fields as property with
getter and setter. Values are extracted from content string or injected in it.

**Examples**:

  ```python
  >>> e = event.Event.set_metadata(
  ...     name="toons", about="None", picture="None", prvkey=k
  ... )
  >>> print(e.content)
- `{'name'` - 'toons', 'about': 'None', 'picture': 'None'}
  >>> e.about = ""
  >>> prnt(e.content)
- `{'name'` - 'toons', 'about': '', 'picture': 'None'}
  ```

