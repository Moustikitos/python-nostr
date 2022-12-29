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
- `tags` _list_ - tag list.
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
                 prvkey: Any[str, pynostr.Keyring] = None)
```

Create a `set metadata` event.

**Arguments**:

- `name` _str_ - nickname to be used by user.
- `about` _str_ - few words about user.
- `picture` _str_ - avatar url (IPFS, URL or base64 data).
- `prvkey` _str or pynostr.Keyring_ - private key to sign the message. if not
  given, it will be asked on terminal.

**Returns**:

- `event.Event` - signed event instance.

<a id="pynostr.event.Event.text_note"></a>

#### text\_note

```python
@staticmethod
def text_note(content: str, prvkey: Any[str, pynostr.Keyring] = None)
```

Create a `text note` event.

**Arguments**:

- `content` _str_ - the text note itself.
- `prvkey` _str or pynostr.Keyring_ - private key to sign the message. if not
  given, it will be asked on terminal.

**Returns**:

- `event.Event` - signed event instance.

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

Compute instance id according to [NIP-01](
https://github.com/nostr-protocol/nips/blob/master/01.md
)

**Returns**:

- `str` - event id.

<a id="pynostr.event.Event.verify"></a>

#### verify

```python
def verify() -> bool
```

Check integrity of event and signature.

**Returns**:

- `bool` - `True` if event is genuine, `False` other else

**Raises**:

- `IntegrityError` - if id does not match with the event. This is to prevent
  issue [`59`](https://github.com/fiatjaf/nostr-tools/issues/59)

<a id="pynostr.event.Event.sign"></a>

#### sign

```python
def sign(prvkey: Any[str, pynostr.Keyring] = None) -> object
```

Sign event.

**Arguments**:

- `prvkey` _str or pynostr.Keyring_ - private key to sign the message. if not
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

- `difficulty` _int_ - level of difficulty to compute the nonce. Number of
  leading `0` for the id is 4 time less than difficulty value.

