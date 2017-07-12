## Sewer          

Sewer is a Let's Encrypt(ACME) client.         
It allows you to obtain ssl/tls certificates from Let's Encrypt.       
Sewer currently only supports the DNS mode of validation. The only currently supported DNS provider is cloudflare but I will add more as time progresses.      


## Usage:

```python
import sewer

# 1. to create a new certificate:
client = sewer.Client(domain_name='example.com',
                      CLOUDFLARE_DNS_ZONE_ID='random',
                      CLOUDFLARE_EMAIL='example@example.com',
                      CLOUDFLARE_API_KEY='nsa-grade-api-key')
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key

print "your certicate is:", certificate
print "your certificate's key is:", certificate_key
print "\n\n"
print "you can write them to a file then add that file to your favourite webserver."

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)

with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)

print "your account key is:", account_key
print "IMPORTANT: keep your account key in a very safe and secure place."

with open('account_key.key', 'w') as account_key_file:
    account_key_file.write(account_key)



# 2. to renew a certificate:
import sewer

with open('account_key.key', 'r') as account_key_file:
    account_key = account_key_file.read()

client = sewer.Client(domain_name='example.com',
                      CLOUDFLARE_DNS_ZONE_ID='random',
                      CLOUDFLARE_EMAIL='example@example.com',
                      CLOUDFLARE_API_KEY='nsa-grade-api-key',
                      account_key=account_key)
certificate = client.renew()
certificate_key = client.certificate_key

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)

with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)
```


## TODO:
- make it DNS provider agnostic
- support more DNS providers
- add robust tests
- be able to handle SAN(subject alternative names)



## FAQ:
- Why another ACME client?          
  I wanted an ACME client that I could use to programmatically(as a library) acquire/get certificates. However I could not 
  find anything satisfactory for use in Python code.
- Why is it called Sewer?
  Because, for the longest time now, getting certificates has felt like wading through sewers. That was before Let's Encrypt showed up.                     
  Also, I really like the Kenyan hip hop artiste going by the name of Kitu Sewer.

