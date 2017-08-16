## Sewer          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ccf655afb3974e9698025cbb65949aa2)](https://www.codacy.com/app/komuW/sewer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=komuW/sewer&amp;utm_campaign=Badge_Grade)
[![CircleCI](https://circleci.com/gh/komuW/sewer/tree/master.svg?style=svg)](https://circleci.com/gh/komuW/sewer/tree/master)
[![codecov](https://codecov.io/gh/komuW/sewer/branch/master/graph/badge.svg)](https://codecov.io/gh/komuW/sewer)


Sewer is a Let's Encrypt(ACME) client.         
It allows you to obtain ssl/tls certificates from Let's Encrypt.       
Sewer currently only supports the DNS mode of validation.                 
The currently supported DNS providers are:         
1. [Cloudflare](https://www.cloudflare.com/dns)               
2. [Aurora](https://www.pcextreme.com/aurora/dns)                 
... but I will add more as time progresses.                 

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
        
usage: sewer [-h] [--version] [--account_key ACCOUNT_KEY] --dns
             {cloudflare,aurora} --domain DOMAIN
             [--alt_domains [ALT_DOMAINS [ALT_DOMAINS ...]]]
             [--bundle_name BUNDLE_NAME] [--endpoint {production,staging}]
             [--email EMAIL] --action {run,renew}

Sewer is a Let's Encrypt(ACME) client.

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed sewer version.
  --account_key ACCOUNT_KEY
                        The path to your letsencrypt/acme account key. eg:
                        --account_key /home/myaccount.key
  --dns {cloudflare,aurora}
                        The name of the dns provider that you want to use.
  --domain DOMAIN       The domain/subdomain name for which you want to
                        get/renew certificate for. eg: --domain example.com
  --alt_domains [ALT_DOMAINS [ALT_DOMAINS ...]]
                        A list of alternative domain/subdomain name/s(if any)
                        for which you want to get/renew certificate for. eg:
                        --alt_domains www.example.com blog.example.com
  --bundle_name BUNDLE_NAME
                        The name to use for certificate certificate key and
                        account key. Default is value of domain.
  --endpoint {production,staging}
                        Whether to use letsencrypt/acme production/live
                        endpoints or staging endpoints. production endpoints
                        are used by default. eg: --endpoint staging
  --email EMAIL         Email to be used for registration and recovery. eg:
                        --email me@example.com
  --action {run,renew}  The action that you want to perform. Either run (get a
                        new certificate) or renew (renew a certificate). eg:
                        --action run
```

The cerrtificate, certificate key and account key will be saved in the directory that you run sewer from.             

The commandline interface(app) is called `sewer` or alternatively you could use, `sewer-cli`.                   


## Features:
- Obtain certificates.
- Renew certificates.
- Supports multiple DNS providers.
- Support for SAN certificates.
- Can be used as a python library as well as a command line(CLI) application.
- Bundling certificates.
- Well written(if I have to say so myself):
  - [Good test coverage](https://codecov.io/gh/komuW/sewer)
  - [Passing continous integration](https://circleci.com/gh/komuW/sewer)
  - [High grade statically analyzed code](https://www.codacy.com/app/komuW/sewer/dashboard)


## TODO:
- support more DNS providers
- https://github.com/komuW/sewer/milestone/1

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
apt-get -y install pandoc && pip install twine wheel pypandoc coverage yapf flake8 mock
```                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add your name and contact(optional) to CONTRIBUTORS.md
- add tests
- format your code using [yapf](https://github.com/google/yapf):                      
```shell
yapf --in-place --recursive --parallel --style "google" .
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

2017-08-03 22:58.16 chosen_dns_provider            message=Using cloudflare as dns provider.
2017-08-03 22:58.16 create_certificate_key         client_name=ACMEclient
2017-08-03 22:58.16 create_csr                     client_name=ACMEclient
2017-08-03 22:58.16 get_certificate_chain          client_name=ACMEclient
2017-08-03 22:58.18 get_certificate_chain_response client_name=ACMEclient status_code=200
2017-08-03 22:58.18 create_account_key             client_name=ACMEclient
2017-08-03 22:58.19 write_account_key              message=account key succesfully written to current directory.
2017-08-03 22:58.19 just_get_me_a_certificate      ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8

2017-08-03 22:58.19 acme_register                  ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8
2017-08-03 22:58.22 acme_register_response         ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] response={u'Status': u'valid', u'agreement': u'https://letsencrypt.org/documents/LE-SA-v1.1.1-August-1-2016.pdf', u'contact': [], u'createdAt': u'2017-08-03T19:58:22.829066395Z',  u'id': 2898386} sewer_client_name=ACMEclient sewer_client_version=0.2.8 status_code=201

2017-08-03 22:58.22 get_challenge                  ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8
2017-08-03 22:58.26 get_challenge_response         ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] response={u'status': u'pending', u'challenges': [{u'status': u'pending', u'token': u'mac1lsAoUqs-3Gyno7k_3NkZ8Ijqpprqq9PTb4mM1wg', u'type': u'dns-01', u'uri': u'https://acme-staging.api.letsencrypt.org/acme/challenge/uOCIaMTnR-MxEtVAdzMtOA95M48f_j1sWEF3qjrvKz0/50674288'}], u'identifier': {u'type': u'dns', u'value': u'example.com'}, u'expires': u'2017-08-10T19:58:26.212741655Z'} sewer_client_name=ACMEclient sewer_client_version=0.2.8 status_code=201

2017-08-03 22:58.26 create_dns_record              dns_provider_name=cloudflare
2017-08-03 22:58.31 create_cloudflare_dns_record_response dns_provider_name=cloudflare response={u'errors': [], u'messages': [], u'result': {u'proxiable': False, u'locked': False, u'name': u'_acme-challenge.example.com', u'created_on': u'2017-08-03T19:58:30.877292Z'}, u'success': True} status_code=200

2017-08-03 22:58.31 notify_acme_challenge_set      ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8
2017-08-03 22:58.35 notify_acme_challenge_set_response ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] response={u'status': u'pending', u'keyAuthorization': u'mac1lsAoUqs-HAJAJAJ.some', u'token': u'mac1lsAoUqs-sdksf', u'type': u'dns-01', u'uri': u'https://acme-staging.api.letsencrypt.org/acme/challenge/uOCIaMTnR-sfsf/50674288'} sewer_client_name=ACMEclient sewer_client_version=0.2.8 status_code=202

2017-08-03 22:58.35 check_challenge                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8
2017-08-03 22:58.40 check_challenge_status_response ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] number_of_checks=1 response={u'status': u'valid', u'validationRecord': [{u'addressesTried': [], u'hostname': u'example.com', u'addressUsed': u'', u'port': u'', u'addressesResolved': []}], u'uri': u'https://acme-staging.api.letsencrypt.org/acme/challenge/xxvx-APOSSSLS/50674288', u'token': u'mac1lsAoUqs-SSSs', u'type': u'dns-01'} sewer_client_name=ACMEclient sewer_client_version=0.2.8 status_code=202

2017-08-03 22:58.40 delete_dns_record              dns_provider_name=cloudflare
2017-08-03 22:58.44 delete_dns_record_response     dns_provider_name=cloudflare response={u'errors': [], u'messages': [], u'result': {u'id': u'06ea612fa03ff12ba95dcf5ba32d7709'}, u'success': True} status_code=200

2017-08-03 22:59.08 get_certificate                ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] sewer_client_name=ACMEclient sewer_client_version=0.2.8
2017-08-03 22:59.12 get_certificate_response       ACME_CERTIFICATE_AUTHORITY_URL=https://acme-staging.api.letsencrypt.org client_name=ACMEclient domain_names=['example.com', 'blog.example.com'] response=Response probably contains a certificate. sewer_client_name=ACMEclient sewer_client_version=0.2.8 status_code=201

2017-08-03 22:59.12 the_end                        message=Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory
```
