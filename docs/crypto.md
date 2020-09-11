## A crypto module for ACME

There were several motivations behind the creation of `crypto.py`:

- a desire to convert the OpenSSL (Python code) usage to the preferred
  cryptography package.

- breaking the Client global mess up into more cohesive components

- Oh, and @jfb's PR adding ECDSA certificate keys was the spark that
triggered the whole thing into [code] motion.

### Preliminaries

I use the term `private key` quite a bit, as it is the term widely used for
some representation of both the public and private parts of an asymmetric
key.

### AcmeKey

`AcmeKey` is a base class for key-type specific classes, but it also carries
shared code that implements most of the methods on the concrete classes. 
These methods use type-specific types or values which are defined on the
concrete classes.

> In fact, it turns out that aside from the CSR, everything sewer needs to
do with crypto can be done after importing just AcmeKey (factory methods and
the methods on the concrete classes the factories hand out).

So now Client and the cli code can stop schlepping around a string that
holds the key in PEM format.  That's part of the reason this work
intentionally broke the names in Client (eg., acct_key in place of account
key) when it switched to an AcmeKey object.

#### Factory methods

Two essential factories:

- `create(key_type: str) -> AcmeKeyType` generates a new private key
  of the named kind.

- `from_bytes(pem_data: bytes) -> AcmeKeyType` returns an AcmeKey object
  containing the key serialized in the PEM bytes, assuming it is one of the
  types of keys that are known (viz., implemented in a subclass of AcmeKey).

And an inessential convenience:

- `from_file(filename: str) -> AcmeKeyType`

#### Attributes

- pk, the private key in the form of cryptography's key class

- kid, the _key identifier_ that comes from registering pk with ACME.

But sewer's code never needs to touch the pk directly, and kid is needed
only for constructing the signed ACME requests.

#### Methods

- `private_bytes(self) -> bytes` Returns all the key's info in PEM format

- `to_file(self, filename:str) -> None` Writes private key to file as PEM

private_bytes is the only method that all ACME clients must use, and that
will often be done indirectly through to_file.

> Note: AcmeKey uses PKCS8 format for private_bytes rather than the
traditional OpenSSL format (PKCS1 for RSA).  This shouldn't be an issue for
anything less artificial than some tests in test_crypto.py <wink>.

- `sign_message(self, message: bytes) -> bytes` Calculate the signature for
  the given message.  (uses SHA256 only because that's what ACME specifies)

- `jwk(self) -> Dict[str, str]`  Returns the JSON Web Key as a dictionary
  (with binary values base64 encoded).  (value is cached)

Sign_message and jwk are methods which an ACME client might find reason to
call, especially if they were implementing a part of the ACME protocol that
sewer currently omits, or a third party extension.

- `set_kid(self, kid: str) -> None`  Hook for ACME register_account or its
  caller to use to attach the registered key's kid to the AcmeKey object.

set_kid is pure implementation detail, a stash for the account's registered
URL on a specific ACME server.  The only use that comes to mind offhand
would be if n ACME client wanted to save and restore this across runs, as it
is not part of the private key PEM file.

### AcmeCsr

This is currently a minimal replacement for the OpenSSL-based create_csr
method.  Which might be all an ACME client requires, so perhaps the current
design will be more or less how it comes out?  There will be an additional
flag for setting the "must be stapled" certificate extension, but there's
really not much else to add, based on a review of the de-facto standard of
cert-bot's options.

One thing to note: yes, the choice of DER format is intentional and
necessary, as the ACME protocol requires that format, base64-url encoded,
_without_ the starting and ending text lines that PEM adds.
