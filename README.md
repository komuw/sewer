## Sewer          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ccf655afb3974e9698025cbb65949aa2)](https://www.codacy.com/app/komuW/sewer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=komuW/sewer&amp;utm_campaign=Badge_Grade)
[![CircleCI](https://circleci.com/gh/komuw/sewer.svg?style=svg)](https://circleci.com/gh/komuw/sewer)
[![codecov](https://codecov.io/gh/komuW/sewer/branch/master/graph/badge.svg)](https://codecov.io/gh/komuW/sewer)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/komuw/sewer)


Sewer is a Let's Encrypt(ACME) client.           
It's name is derived from Kenyan hip hop artiste, Kitu Sewer.                        
It allows you to obtain ssl/tls certificates from Let's Encrypt.       

> Let’s Encrypt is a free, automated, and open Certificate Authority. - https://letsencrypt.org

Sewer currently only supports the DNS mode of validation, I have no plans of supporting other modes of validation.                 
The currently supported DNS providers are:         
1. [Cloudflare](https://www.cloudflare.com/dns)               
2. [Aurora](https://www.pcextreme.com/aurora/dns)                 
3. [acme-dns](https://github.com/joohoi/acme-dns)
4. [Aliyun](https://help.aliyun.com/document_detail/29739.html)
5. [He DNS, Hurricane Electric DNS](https://dns.he.net/)
6. [Rackspace](https://www.rackspace.com/cloud/dns)
7. [DNSPod](https://www.dnspod.cn/)
8. [DuckDNS](https://www.duckdns.org/)
9. [ClouDNS](https://www.cloudns.net)
10. [AWS rout353](https://aws.amazon.com/route53/)
11. [Bring your own dns provider](#bring-your-own-dns-provider)
...

Sewer can be used very easliy programmatically as a library from code.            
Sewer also comes with a command-line(cli) interface(app) that you can use from your favourite terminal           

For a changelog(release notes), see: https://github.com/komuw/sewer/releases

## Installation

```shell
pip3 install sewer

# with All DNS Provider support, include aliyun, Hurricane Electric, Aurora, ACME ...
# pip3 install sewer[alldns]

# with Cloudflare support
# pip3 install sewer[cloudflare]

# with Aliyun support
# pip3 install sewer[aliyun]

# with HE DNS(Hurricane Electric DNS) support
# pip3 install sewer[hurricane]

# with Aurora DNS Support
# pip3 install sewer[aurora]

# with ACME DNS Support
# pip3 install sewer[acmedns]

# with Rackspace DNS Support
# pip3 install sewer[rackspace]

# with DNSPod DNS Support
# pip3 install sewer[dnspod]

# with DuckDNS DNS Support
# pip3 install sewer[duckdns]

# with ClouDNS DNS Support
# pip3 install sewer[cloudns]

# with AWS route53 DNS Support
# pip3 install sewer[route53]
```

sewer(since version 0.5.0) is now python3 only. To install the (now unsupported) python2 version, run;

```shell
pip install sewer==0.3.0
```
Sewer is in active development and it's API may change in backward incompatible ways.               
[https://pypi.python.org/pypi/sewer](https://pypi.python.org/pypi/sewer)


## Usage

```python
import sewer

dns_class = sewer.CloudFlareDns(CLOUDFLARE_EMAIL='example@example.com',
                                CLOUDFLARE_API_KEY='nsa-grade-api-key')

# 1. to create a new certificate:
client = sewer.Client(domain_name='example.com',
                      dns_class=dns_class)
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
import sewer

dns_class = sewer.CloudFlareDns(CLOUDFLARE_EMAIL='example@example.com',
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

# 3. You can also request/renew wildcard certificates:
import sewer
dns_class = sewer.CloudFlareDns(CLOUDFLARE_EMAIL='example@example.com',
                                CLOUDFLARE_API_KEY='nsa-grade-api-key')
client = sewer.Client(domain_name='*.example.com',
                      dns_class=dns_class)
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key
```


## CLI
Sewer also ships with a commandline interface(called `sewer` or `sewer-cli`) that you can use to get/renew certificates.            
Your dns providers credentials need to be supplied as environment variables.
 
To get certificate, run:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_API_KEY=api-key \
sewer \
--dns cloudflare \
--domain example.com \
--action run
```              

To renew a certificate, run:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_API_KEY=api-key \
sewer \
--account_key /path/to/your/account.key \
--dns cloudflare \
--domain example.com \
--action renew
```              

To see help:
```shell
sewer --help                 
        
usage: sewer [-h] [--version] [--account_key ACCOUNT_KEY]
             [--certificate_key CERTIFICATE_KEY] --dns
             {cloudflare,aurora,acmedns,aliyun,hurricane} --domain DOMAIN
             [--alt_domains [ALT_DOMAINS [ALT_DOMAINS ...]]]
             [--bundle_name BUNDLE_NAME] [--endpoint {production,staging}]
             [--email EMAIL] --action {run,renew} [--out_dir OUT_DIR]
             [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Sewer is a Let's Encrypt(ACME) client.

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed sewer version.
  --account_key ACCOUNT_KEY
                        The path to your letsencrypt/acme account key. eg:
                        --account_key /home/myaccount.key
  --certificate_key CERTIFICATE_KEY
                        The path to your certificate key. eg:
                        --certificate_key /home/mycertificate.key
  --dns {cloudflare,aurora,acmedns,aliyun,hurricane}
                        The name of the dns provider that you want to use.
  --domain DOMAIN       The domain/subdomain name for which you want to
                        get/renew certificate for. wildcards are also
                        supported eg: --domain example.com
  --alt_domains [ALT_DOMAINS [ALT_DOMAINS ...]]
                        A list of alternative domain/subdomain name/s(if any)
                        for which you want to get/renew certificate for. eg:
                        --alt_domains www.example.com blog.example.com
  --bundle_name BUNDLE_NAME
                        The name to use for certificate certificate key and
                        account key. Default is name of domain.
  --endpoint {production,staging}
                        Whether to use letsencrypt/acme production/live
                        endpoints or staging endpoints. production endpoints
                        are used by default. eg: --endpoint staging
  --email EMAIL         Email to be used for registration and recovery. eg:
                        --email me@example.com
  --action {run,renew}  The action that you want to perform. Either run (get a
                        new certificate) or renew (renew a certificate). eg:
                        --action run
  --out_dir OUT_DIR     The dir where the certificate and keys file will be
                        stored. default: The directory you run sewer command.
                        eg: --out_dir /data/ssl/
  --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The log level to output log messages at. eg:
                        --loglevel DEBUG
```

The cerrtificate, certificate key and account key will be saved in the directory that you run sewer from.             

The commandline interface(app) is called `sewer` or alternatively you could use, `sewer-cli`.                   



## Features
- Obtain certificates.
- Renew certificates.
- Supports multiple DNS providers.
- Supports wildcard certificates
- Supports acme version 2 only.
- [Bring your own dns provider](#bring-your-own-dns-provider) 
- Support for SAN certificates.
- Can be used as a python library as well as a command line(CLI) application.
- Bundling certificates.
- Well written(if I have to say so myself):
  - [Good test coverage](https://codecov.io/gh/komuW/sewer)
  - [Passing continous integration](https://circleci.com/gh/komuW/sewer)
  - [High grade statically analyzed code](https://www.codacy.com/app/komuW/sewer/dashboard)

## Bring your own DNS provider          
It is very easy to use any dns provider with sewer.          
All you have to do is create your own dns class that is a child class of [`sewer.BaseDns`](https://github.com/komuw/sewer/blob/master/sewer/dns_providers/common.py) and then implement the             
`create_dns_record` and `delete_dns_record` methods.                     
As an example, if you wanted to use [AWS route53](https://aws.amazon.com/route53/) as your dns provider with sewer, you            
would do something like;
```python
import sewer
import boto3


class AWSroute53Dns(sewer.BaseDns):
    def __init__(self,
                 HostedZoneId,
                 AWS_ACCESS_KEY_ID,
                 AWS_SECRET_ACCESS_KEY):
        self.dns_provider_name = 'AWS_route53'
        self.HostedZoneId = HostedZoneId
        self.boto_client = boto3.client(
            'route53', aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        super(AWSroute53Dns, self).__init__()

    def create_dns_record(self,
                          domain_name,
                          domain_dns_value):
        """
        AWS route53 with boto3 documentation;
        https://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets
        """
        # do whatever is necessary for your particular DNS provider to create a TXT DNS record
        # eg for AWS route53, it will be something like::
        self.boto_client.change_resource_record_sets(
            HostedZoneId=self.HostedZoneId,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': '_acme-challenge' + '.' + domain_name + '.',
                            'Type': 'TXT',
                            'TTL': 123,
                            'ResourceRecords': [
                                {
                                    'Value': "{0}".format(domain_dns_value)},
                            ]}},
                ]})

    def delete_dns_record(self,
                          domain_name,
                          domain_dns_value):
        # do whatever is necessary for your particular DNS provider to delete a TXT DNS record
        # eg for AWS route53, it will be something like::
        self.boto_client.change_resource_record_sets(
            HostedZoneId=self.HostedZoneId,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': '_acme-challenge' + '.' + domain_name + '.',
                            'Type': 'TXT',
                            'TTL': 123,
                            'ResourceRecords': [
                                {
                                    'Value': "{0}".format(domain_dns_value)},
                            ]}},
                ]})


custom_route53_dns_class = AWSroute53Dns(
    HostedZoneId='my-zone', AWS_ACCESS_KEY_ID='access-key',
    AWS_SECRET_ACCESS_KEY='secret-access-key')

# create a new certificate:
client = sewer.Client(domain_name='example.com',
                      dns_class=custom_route53_dns_class)
certificate = client.cert()
certificate_key = client.certificate_key
account_key = client.account_key
print("certificate::", certificate)
print("certificate's key::", certificate_key)
```

## Development setup
see the how to contribute [documentation](https://github.com/komuw/sewer/blob/master/.github/CONTRIBUTING.md)                



## TODO
- support more DNS providers
- https://github.com/komuw/sewer/milestone/1

## FAQ
- Why another ACME client?          
  I wanted an ACME client that I could use to programmatically(as a library) acquire/get certificates. However I could not 
  find anything satisfactory for use in Python code.
- Why is it called Sewer?
  I really like the Kenyan hip hop artiste going by the name of Kitu Sewer.                            


Here's the ouput of running sewer using the cli app:                
```shell
CLOUDFLARE_EMAIL=example@example.com \
CLOUDFLARE_API_KEY=nsa-grade-api-key \
sewer \
--endpoint staging \
--dns cloudflare \
--domain subdomain.example.com \
--action run            

2018-03-06 18:08.41 chosen_dns_provider            message=Using cloudflare as dns provider.

2018-03-06 18:08.46 acme_register                  acme_server=https://acme-staging... domain_names=['subdomain.example.com'] sewer_version=0.5.0b
2018-03-06 18:08.52 acme_register_response         acme_server=https://acme-staging... domain_names=['subdomain.example.com']

2018-03-06 18:08.52 apply_for_cert_issuance        acme_server=https://acme-staging... domain_names=['subdomain.example.com'] sewer_version=0.5.0b
2018-03-06 18:09.01 apply_for_cert_issuance_response acme_server=https://acme-staging... domain_names=['subdomain.example.com']

2018-03-06 18:09.08 create_dns_record              dns_provider_name=CloudFlareDns
2018-03-06 18:09.16 create_cloudflare_dns_record_response dns_provider_name=CloudFlareDns status_code=200

2018-03-06 18:09.36 send_csr                       acme_server=https://acme-staging... domain_names=['subdomain.example.com'] sewer_version=0.5.0b
2018-03-06 18:09.45 send_csr_response              acme_server=https://acme-staging... domain_names=['subdomain.example.com']

2018-03-06 18:09.45 download_certificate           acme_server=https://acme-staging... domain_names=['subdomain.example.com'] sewer_version=0.5.0b
2018-03-06 18:09.50 download_certificate_response  acme_server=https://acme-staging... domain_names=['subdomain.example.com']

2018-03-06 18:09.54 the_end                        message=Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory
```

