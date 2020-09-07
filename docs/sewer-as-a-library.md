# Sewer as a Python Library

>`sewer-the-library` is in a period of heavy change (summer 2020 - ?).  I'll
try to keep the examples (below) and other docs up to date, but I'm sure
things will lag sometimes.

This document is neither a "cookbook" nor in any way a substitute for the
documentation of sewer's parts and internals, such as they are.  Let's try
to list the existing docs:

- [Cryptographic library](crypto) this is in decent shape because it's been
  created and kept up to date in sync with crypto.py - both too new to have
  bit rot yet.

- [ACME protocol](ACME) was a piece I started writing while learning the
  quirks of the ACMEprotocol.  Quite incomplete, the main thing it brings to
  the table is the link to RFC8555, which is the protocol's definition.  Of
  course there are other foundational RFCs to be read...

- The [driver catalog](catalog) is another new part that isn't yet being
  used to its fullest.  It glues the drivers and the CLI program together,
  and stands ready to help your bespoke front end likewise unless your
  target is so specific you can just manually import the only driver you
  need.

- Drivers!  So much of this is about those intermediaries between sewer and
  the diverse services that actually publish our challenge responses.

  + [Unified provider](UnifiedProvider) began as a technical essay when I
    was starting to sort through the problems and possibilities Alec's
    original http-01 driver support introduced.  It's an uneven blend of
    design philosophy and code documentation, with plenty of ToDo in it.

  + [Wildcard certificates](wildcards) are one of the things the dns-01
    challenge type brought to the table.  Some notes on how they work and
    what issues remain.

  + [Aliasing](Aliasing) can be a handy technique to manage dns-01
    challenges without needing to deal with a primary DNS provider whose
    support for fast-propagating, short-lived TXT records leaves something
    to be desired.
  + Speaking of DNS Propagation, we find [DNS propagation](DNS-Propagation),
    which talks about what it is and why you might need it, and offers what
    documentation there is on the parameters to pass to the drivers to
    control it.  And for driver writers, mostly,
    [unpropagated](unpropagated) discusses what's needed to add a probe &
    wait timeout loop.

_more to do <sigh>_

## Usage examples

Keep in mind that these are untested code intended to demonstrate how the
major features are used.  Supporting details may not be repeated for each
similar example, or may not be present in any of them.

```python
import sewer.client
from sewer.crypto import AcmeKey

# [[ change this to load using the catalog! ]]
import sewer.dns_providers.cloudflare

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)

# 1. to create a new certificate (new account and certificate keys)

client = sewer.client.Client(
    domain_name='example.com',
    dns_class=dns_class,
    acct_key=AcmeKey.create("rsa2048"),
    cert_key=AcmeKey.create("rsa2048")
)
certificate = client.cert()

# NB: new crypto keeps keys & certs in python objects.  They intentionally
# do not convert to printable form automatically (__str__, etc.)

print("your certificate is:", certificate.private_bytes())
print("your certificate's key is:", cert_key.private_bytes())
print("your letsencrypt.org account key is:", acct_key.private_bytes())

# NB: your certificate_key and account_key should be SECRET.
# You can write these out to individual files, eg::

with open("certificate.crt", "wb"') as f:
    f.write(certificate.private_bytes())
with open('certificate.key', 'wb') as f:
    f.write(certkey.private_bytes())
with open('account.key', 'w') f:
    f.write(acctkey.private_bytes())

# the acct_key also contains ACME's "kid" identifier if you're interested

# 2. to renew a certificate:

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)

# load saved keys or create new as you prefer
acct_key = AcmeKey.from_file("account.key")
cert_key = AcmeKey.from_file("certificate_key")

client = sewer.client.Client(
    domain_name='example.com',
    dns_class=dns_class,
    acct_key=acct_key,
    cert_key=cert_key,
)
certificate = client.renew()
certificate_key = client.certificate_key

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)
with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)

# 3. You can also request/renew wildcard certificates:

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)
client = sewer.client.Client(
    domain_name='*.example.com',
    dns_class=dns_class,
    # load or create keys
)
certificate = client.cert()
cert_key = client.cert_key
acct_key = client.acct_key
```
