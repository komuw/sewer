## USAGE - sewer as a Python library

### Basic usage example

```python
import sewer.client
import sewer.dns_providers.cloudflare

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)

# 1. to create a new certificate:
client = sewer.client.Client(
    domain_name='example.com',
    dns_class=dns_class
)
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key

print("your certificate is:", certificate)
print("your certificate's key is:", certificate_key)
print("your letsencrypt.org account key is:", account_key)
# NB: your certificate_key and account_key should be SECRET.
# keep them very safe.

# you can write these out to individual files, eg::

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)
with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)
with open('account_key.key', 'w') as account_key_file:
    account_key_file.write(account_key)


# 2. to renew a certificate:
import sewer.client
import sewer.dns_providers.cloudflare

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)

with open('account_key.key', 'r') as account_key_file:
    account_key = account_key_file.read()

client = sewer.client.Client(
    domain_name='example.com',
    dns_class=dns_class,
    account_key=account_key
)
certificate = client.renew()
certificate_key = client.certificate_key

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)
with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)

# 3. You can also request/renew wildcard certificates:
import sewer.client
import sewer.dns_providers.cloudflare

dns_class = sewer.dns_providers.cloudflare.CloudFlareDns(
    CLOUDFLARE_EMAIL='example@example.com',
    CLOUDFLARE_API_KEY='nsa-grade-api-key'
)
client = sewer.client.Client(
    domain_name='*.example.com',
    dns_class=dns_class
)
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key
```

### Bring your own HTTP provider

**To be rewritten.**  For now, see `providers/demo.py` for some hints, and
[UnifiedProviders](UnifiedProviders) for doumentation of the interface.
