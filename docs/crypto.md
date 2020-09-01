## A crypto module for ACME

There wer several motivations behind the creation of `crypto.py`:

- a desire to convert the OpenSSL (Python code) usage to the preferred
  cryptography package.

- breaking the Client global mess up into more cohesive components

- .  Oh, and @jfb's work on adding ECDSA certificate keys
was the spark that triggered the whole thing into [code] motion.

### AcmeKey

`AcmeKey` is a base class for key-type specific classes, but it also carries
shared code that both of the current type-specific classes, `AcmeRsaKey` and
`AcmeEcKey` share the use of.  Much of this uses type-specific types or
values which are defined on the subclasses.

#### Attributes

- pk, the private key in the form of cryptography's key class

- kid, the _key identifier_ that comes from registering pk with ACME.

#### Methods

- `set_kid(self, kid: str) -> None`  Hook for ACME register_account or its
  caller to use to attach the registered key's kid to the AcmeKey object.

- `private_bytes(self) -> bytes` Returns all the key's info in PEM format

- `sign_message(self, message: bytes) -> bytes` Calculate the signature for
  the given message.  (uses SHA256 only because that's what ACME specifies)

- `jwk(self) -> Dict[str, str]`  Returns the JSON Web Key as a dictionary
  (with binary values base64 encoded).  (value is cached)

#### Other AcmeKey module-level bits

Two factory methods for AcmeKey (these might become class methods of
AcmeKey?):

- `new_ACME_key(key_type: str) -> AcmeKey`

- `load_ACME_key(pem_data: bytes) -> AcmeKey`

### AcmeCsr

This is currently a minimal replacement for the OpenSSL-based create_csr
method.  Which might be all an ACME client requires, so perhaps the current
design will be more or less how it comes out?  There will be an additional
flag for setting the "must be stapled" certificate extension, but there's
really not much else to add, based on a review of the de-facto standard of
cert-bot's options.

One thing to note: yes, the choice of DER format is intentional and
necessary, as the protocol requires that, base64-url encoded, _without_ the
starting and ending text lines that PEM wraps that same encoding in.
