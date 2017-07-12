## Sewer          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ccf655afb3974e9698025cbb65949aa2)](https://www.codacy.com/app/komuW/sewer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=komuW/sewer&amp;utm_campaign=Badge_Grade)
[![CircleCI](https://circleci.com/gh/komuW/sewer/tree/master.svg?style=svg)](https://circleci.com/gh/komuW/sewer/tree/master)


Sewer is a Let's Encrypt(ACME) client.         
It allows you to obtain ssl/tls certificates from Let's Encrypt.       
Sewer currently only supports the DNS mode of validation. The only currently supported DNS provider is cloudflare but I will add more as time progresses.      


## Installation:

`pip install sewer`


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
- add ci



## FAQ:
- Why another ACME client?          
  I wanted an ACME client that I could use to programmatically(as a library) acquire/get certificates. However I could not 
  find anything satisfactory for use in Python code.
- Why is it called Sewer?
  Because, for the longest time now, getting certificates has felt like wading through sewers. That was before Let's Encrypt showed up.                     
  Also, I really like the Kenyan hip hop artiste going by the name of Kitu Sewer.


## Development setup
- fork this repo.
- cd sewer
- sudo apt-get install pandoc
- open an issue on this repo. In your issue, outline what it is you want to add and why.
- install pre-requiste software:             
`apt-get install pandoc && pip install twine wheel pypandoc coverage yapf flake8`                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add your name and contact(optional) to 
- add tests
- run tests to make sure they are passing
- format your code using [yapf](https://github.com/google/yapf):                      
`yapf --in-place --style "google" -r .`                     
- run [flake8](https://pypi.python.org/pypi/flake8) on the code and fix any issues:                      
`flake8 .`                      
- open a pull request on this repo.               

NB: I make no commitment of accepting your pull requests.
