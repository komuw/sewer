## USAGE - sewer as a Python library

### Basic usage example

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

### Bring your own HTTP provider

**To be rewritten.**  For now, see `providers/demo.py` for some hints, and
[UnifiedProviders](UnifiedProviders) for doumentation of the interface.
