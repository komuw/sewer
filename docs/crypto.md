# A crypto module for ACME

There were several motivations behind the creation of `crypto.py`:

- a desire to convert the OpenSSL (Python code) usage to the preferred
  cryptography package.  Note that this is only a change in which Python
  wrapper around the openssl binary is used!

- breaking the Client global mess up into more cohesive components

- Oh, and @jfb's PR adding ECDSA certificate keys was the spark that
  triggered the whole thing into [code] motion.

## Preliminaries

I use the term `private key` quite a bit, as it is the term widely used for
some representation of both the public and private parts of an asymmetric
key.

## AcmeKey

`AcmeKey` is a parameterized holder for the primitive key classes of the
underlying implementation (the cryptography package).

So now Client and the cli code can stop schlepping around a string that
holds the key in PEM format.  That's part of the reason this work
intentionally broke the names in Client (eg., acct_key in place of account
key) when it switched to an AcmeKey object.

#### Factory (class)methods

Two essential factories:

- `create(key_type: str) -> AcmeKeyType` generates a new private key
  of the named kind.

- `from_pem(pem_data: bytes) -> AcmeKeyType` returns an AcmeKey object
  containing the key serialized in the PEM bytes, assuming it is one of the
  types of keys that are known (viz., implemented in a subclass of AcmeKey).

And an inessential convenience:

- `read_pem(filename: str) -> AcmeKeyType` loads the key from a PEM format
  file.

### AcmeKey attributes

- pk, the private key in the form of cryptography's key class

Sewer's code never needs to touch the pk directly.

### AcmeKey methods

- `to_pem(self) -> bytes` Returns all the key's info in PEM format

- `write_pem(self, filename:str) -> None` Writes private key to file as PEM

private_bytes is the only method that all ACME clients must use, and that
will often be done indirectly through to_file.

- `sign_message(self, message: bytes) -> bytes` Calculate the signature for
  the given message.  (uses SHA256 only because that's what ACME specifies)

> You will have noticed the symmetry of the method names: to/from_pem for
  in-memory byte strings, read/write_pem for keys in files.

## AcmeAccount

Accounts are keys which are registered with the ACME service and thereafter
used to identify and authenticate the origina of most of the messages sent
to the service.  They are a subclass of AcmeKey that extends the interface
to include things only an account key has to do.

### AcmeAccount attributes

- _kid: str — the _key identifier_ that comes from registering pk with ACME.

- _timestamp: float — when the account was [most recently] registered

- _jwk: Dict[str, str] — cached JWK or None

_kid is needed only for constructing the signed ACME requests, and is used
mostly as an in-memory value.  There is experimental support for saving the
Key ID and timestamp along with the account key.

### AcmeAccount methods

- `jwk(self) -> Dict[str, str]`  Returns the JSON Web Key as a dictionary
  (with binary values base64 encoded).  (value is cached)

- `set_kid(self, kid: str, timestamp: float = None) -> None`  Hook for ACME
  register_account or its caller to use to attach the registered key's kid
  to the AcmeKey object.  If timestamp is not given, the current time will
  be used.

set_kid() is pure implementation detail, a stash for the account's registered
URL on a specific ACME server.  timestamp is what time.time() returns.

> not yet implemented: write_extended_pem, read_extended_pem (or will read
  just be an override that loads the extended values if present?)


## AcmeCsr

This is currently a minimal replacement for the OpenSSL-based create_csr
method.  Which might be all an ACME client requires, so perhaps the current
design will be more or less how it comes out?  There will be an additional
flag for setting the "must be stapled" certificate extension, but there's
really not much else to add, based on a review of the de-facto standard of
cert-bot's options.

One thing to note: yes, the choice of DER format is intentional and
necessary, as the ACME protocol requires that format, base64-url encoded,
_without_ the starting and ending text lines that PEM adds.
