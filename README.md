## Sewer          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ccf655afb3974e9698025cbb65949aa2)](https://www.codacy.com/app/komuW/sewer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=komuW/sewer&amp;utm_campaign=Badge_Grade)
[![CircleCI](https://circleci.com/gh/komuW/sewer/tree/master.svg?style=svg)](https://circleci.com/gh/komuW/sewer/tree/master)
[![codecov](https://codecov.io/gh/komuW/sewer/branch/master/graph/badge.svg)](https://codecov.io/gh/komuW/sewer)


Sewer is a Let's Encrypt(ACME) client.         
It allows you to obtain ssl/tls certificates from Let's Encrypt.       
Sewer currently only supports the DNS mode of validation. The only currently supported DNS provider is cloudflare but I will add more as time progresses.         
Sewer can be used very easliy programmatically as a library from code.            
Sewer also comes with a command-line(cli) interface(app) that you can use from your favourite terminal           


## Installation:

```shell
pip install sewer
```           
Sewer is in active development and it's API may change in backward incompatible ways.               
[https://pypi.python.org/pypi/sewer](https://pypi.python.org/pypi/sewer)


## Usage:

```python
import sewer

dns_class = sewer.CloudFlareDns(CLOUDFLARE_DNS_ZONE_ID='random',
                                CLOUDFLARE_EMAIL='example@example.com',
                                CLOUDFLARE_API_KEY='nsa-grade-api-key')

# 1. to create a new certificate:
client = sewer.Client(domain_name='example.com',
                      dns_class=dns_class)
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key

print "your certificate is:", certificate
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

dns_class = sewer.CloudFlareDns(CLOUDFLARE_DNS_ZONE_ID='random',
                                CLOUDFLARE_EMAIL='example@example.com',
                                CLOUDFLARE_API_KEY='nsa-grade-api-key')

with open('account_key.key', 'r') as account_key_file:
    account_key = account_key_file.read()

client = sewer.Client(domain_name='example.com',
                      dns_class=dns_class,
                      account_key=account_key)
certificate = client.renew()
certificate_key = client.certificate_key

with open('certificate.crt', 'w') as certificate_file:
    certificate_file.write(certificate)

with open('certificate.key', 'w') as certificate_key_file:
    certificate_key_file.write(certificate_key)
```


## CLI:
Sewer also ships with a commandline interface(called `sewer` or `sewer-cli`) that you can use to get/renew certificates.            
Your dns providers credentials need to be supplied as environment variables.
 
To get certificate, run:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_DNS_ZONE_ID=some-zone \
CLOUDFLARE_API_KEY=api-key \
sewer \
--dns cloudflare \
--domains example.com \
--action run
```              

To renew a certificate, run:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_DNS_ZONE_ID=some-zone \
CLOUDFLARE_API_KEY=api-key \
sewer \
--account_key /path/to/your/account.key \
--dns cloudflare \
--domains example.com \
--action renew
```              

To see help:
```shell
sewer --help                 
     
usage: sewer [-h] [--account_key ACCOUNT_KEY] --dns {cloudflare} --domains
             DOMAINS [--bundle_name BUNDLE_NAME] --action {run,renew}

Sewer is a Let's Encrypt(ACME) client.

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed sewer version.
  --account_key ACCOUNT_KEY
                        The path to your letsencrypt/acme account key.
  --dns {cloudflare}    The name of the dns provider that you want to use.
  --domains DOMAINS     The domain/subdomain name for which you want to
                        get/renew certificate for.
  --bundle_name BUNDLE_NAME
                        The name to use for certificate certificate key and
                        account key. Default is value of domains.
  --endpoint {production,staging}
                        Whether to use letsencrypt/acme production/live
                        endpoints or staging endpoints. production endpoints
                        are used by default.
  --email EMAIL         Email to be used for registration and recovery.
  --action {run,renew}  The action that you want to perform. Either run (get a
                        new certificate) or renew (renew a certificate).
```

The cerrtificate, certificate key and account key will be saved in the directory that you run sewer from.             

The commandline interface(app) is called `sewer` or alternatively you could use, `sewer-cli`.                   

## TODO:
- support more DNS providers
- be able to handle SAN(subject alternative names)


## FAQ:
- Why another ACME client?          
  I wanted an ACME client that I could use to programmatically(as a library) acquire/get certificates. However I could not 
  find anything satisfactory for use in Python code.
- Why is it called Sewer?
  Because, for the longest time now, getting certificates has felt like wading through sewers. That was before Let's Encrypt showed up.                     
  Also, I really like the Kenyan hip hop artiste going by the name of Kitu Sewer.


## Development setup:
- fork this repo.
- cd sewer
- sudo apt-get install pandoc
- open an issue on this repo. In your issue, outline what it is you want to add and why.
- install pre-requiste software:             
```shell
apt-get install pandoc && pip install twine wheel pypandoc coverage yapf flake8 mock
```                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add your name and contact(optional) to CONTRIBUTORS.md
- add tests
- run tests to make sure they are passing
- format your code using [yapf](https://github.com/google/yapf):                      
```shell
yapf --in-place --style "google" -r .
```                     
- run [flake8](https://pypi.python.org/pypi/flake8) on the code and fix any issues:                      
```shell
flake8 .
```                      
- run tests and make sure everything is passing:
```shell
make test
```
- open a pull request on this repo.               
NB: I make no commitment of accepting your pull requests.                 



Here's the ouput of running sewer using the cli app:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_DNS_ZONE_ID=random \
CLOUDFLARE_API_KEY=nsa-grade-api-key \
sewer \
--endpoint staging \
--dns cloudflare \
--domains subdomain.example.com \
--action run            

2017-07-14 18:09.55 chosen_dns_provider            message=Using cloudflare as dns provider.
2017-07-14 18:09.55 create_certificate_key         client_name=ACMEclient
2017-07-14 18:09.55 create_csr                     client_name=ACMEclient
2017-07-14 18:09.55 get_certificate_chain          client_name=ACMEclient
2017-07-14 18:09.56 create_account_key             client_name=ACMEclient
2017-07-14 18:09.56 just_get_me_a_certificate      ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.56 acme_register                  ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.56 make_signed_acme_request       ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.56 get_acme_header                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.58 sign_message                   ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.59 get_challenge                  ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.59 make_signed_acme_request       ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:09.59 get_acme_header                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.02 sign_message                   ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.04 get_keyauthorization           ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.04 get_acme_header                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.08 notify_acme_challenge_set      ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.08 make_signed_acme_request       ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.08 get_acme_header                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.10 sign_message                   ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.11 check_challenge                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.19 get_certificate                  ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.19 make_signed_acme_request       ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.19 get_acme_header                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.21 sign_message                   ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_name=subdomain.example.com
2017-07-14 18:10.22 the_end                        message=Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory
```
