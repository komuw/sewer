# `sewer` changelog:

## **pre-release** 0.8.5

- driver for Windows DNS server (local only) [IN PROGRESS]

- cleanup that was deferred from 0.8.4 (affects developers, not cli users)

  - crypto.py refactored

  - mypy added to tests

    - dns_providers have had non-base imports cleaned up: use local `# type:
      ignore` annotations

    - a few non-service-specific libs marked globally to be ignored

  - REMOVED obsolescent dns_provider_name class variables (use the JSON
    catalog, added in 0.8.3)

  - REMOVED obsolescent guards around service-specific imports and the
    corresponding delayed exceptions (the unnecessary imports that used to
    require the guards were removed in 0.8.3)

  - crypto.py's tests migrated to pytest format as tests/crypto_test.py

- Fixed the alias support code and unbound_ssh, its only in-tree client, to
  use correct names for alias option parameters

- Aliasing document updated to current client options

- in-tree tests began migrating to pytest format (and moving to ./tests)

## **version:** 0.8.4

- add support for ECDSA keys

CLI changes:

- `--acct_key` & `--cert_key` should be used to designate the file that
  holds the keys to be used (rather than having new ones generated). 
  `--account_key` & `--certificate_key` are still accepted as synonyms.

- add `--acct_key_type` & `--cert_key_type` to allow choice of RSA or EC
  keys and key sizes when sewer is generating them for you.

- changed default for generated keys to 3072 bit RSA (had been 2048 bit)

- add `--is_new_key` to allow for first-time registration of your own
  account key (using `--acct_key`) generated outside of sewer.

Internal changes for library clients:

- Client methods cert() and renew() are deprecated; just call
  get_certificate() directly instead.

- Client **no longer generates keys**.  (see below)

- crytographic refactoring

  - AcmeKey, AcmeAccount & AcmeCsr in crypto.py; uses only cryptography library

- Client interface changes due to crypto refactoring

  - dropped `account_key` and `certificate_key` optional arguments to Client

  - added `acct_key` and `cert_key` REQUIRED arguments to Client taking
    AcmeAccount and AcmeKey objects, respectively.

  - add `is_new_acct` argument to force registration of the supplied account
    key

  - dropped `bits` argument because Client no longer generates keys!

  - dropped `digest` argument since there are currently no alternate digest
    methods for the different key types.  (was this ever used?)

## **version:** 0.8.3

Features and Improvements:
- added `--acme-timeout <seconds>` option to adjust timeout on queries to
  the ACME server
- `--action {run,renew}` has been doing nothing useful and is now deprecated.
- added `--p_opt <name>=<value>` for passing kwargs to drivers
- Added optional parameters accepted by base class for DNS drivers:
  - `alias=<alias_domain>` specifies a separate domain for DNS challenges
    (requires driver support, see [Aliasing](Aliasing))
  - `prop_delay=<seconds>` gives a fixed delay (sleep) after challenge setup
- gandi (legacy DNS driver) fixed internal bugs that broke common wildcard
  use cases (eg., `*.domain.tld`) as well as the "wildcard plus" pattern
- added unbound_ssh legacy-style DNS provider as a working demo of adding
  new features to legacy drivers.  It does work in the right environment, and
  could be useful to someone other than myself (mm).

Internals:
- added [catalog.py](catalog) to manage provider catalogs; includes
  get_provider(name) method to replace `import ......{name.}ClassName`
- replace __version__.py with meta.json; setup.py converted; add sewer_meta()
  in lib.py; cli.py converted; client.py converted
- added catalog.json defining known drivers and their interfaces; also
  information about dependencies for setup.py
- added `**kwargs` to all legacy providers to allow new options that are
  handled in a parent class to pass through (for `alias`, `prop_delay`, etc.)
- removed imports that were in `sewer/__init__` and
  `sewer/dns_providers/__init__`; fixed all uses in cli.py and tests.
- began cleanup/refactor of cli.py (there will be more to come and/or a new,
  more config driven, alternative command (0.9?))
- added `__main__.py` to support `python -m sewer` invocation of `sewer-cli`
- fixed imports in client.py that didn't actually import the parts of
  OpenSSL and cryptography that we use (worked because we import requests?)

See also [release notes](notes/0.8.3-notes).

## **version:** 0.8.2
Feature additions:

- support current RFC8555 protocol (LE staging current, production requires in Nov)
- added DNS providers powerdns and gandi

Internals (features and/or annoying changes for sewer-as-a-library users)

- unified dns-01 and http-01 providers; support challenge propagation check
- added support for non-dns (http-01 challenge) provider
- collect shared (internal) functions into lib.py
- use unitest.mock rather than external module
- client no longer prepends`*.` to wildcards; remove spotty code in providers to strip it
- begin addition of annotations, mostly opportunistically

See also [release notes](notes/0.8.2-notes).

## **version:** 0.8.1
- Fix bug where `sewer` was unable to delete wildcard names from clouflare: https://github.com/komuw/sewer/pull/139    
- Fix a StopIteration bug: https://github.com/komuw/sewer/pull/148   
- Add guide on how to create a new pypi release

## **version:** 0.8.0
- Fix bug where `sewer` would log twice: https://github.com/komuw/sewer/pull/137  
  Thanks to [@mmaney](https://github.com/mmaney) for this

## **version:** 0.7.9
- Fix bug where Aliyun response is in bytes: https://github.com/komuw/sewer/pull/133     
  Thanks to [@ButterflyTech](https://github.com/ButterflyTech) for this   

## **version:** 0.7.8
- Add support for Cloudflare token auth: https://github.com/komuw/sewer/pull/130       
  Thanks to [@moritz89](https://github.com/moritz89) for this   

## **version:** 0.7.7
- Add support for Support AWS Route53: https://github.com/komuw/sewer/pull/126      
  Thanks to [@soloradish](https://github.com/soloradish) for this

## **version:** 0.7.6
- Fix logging, sewer was redefining root logger: https://github.com/komuw/sewer/pull/125  
  Thanks to [@etienne-napoleone](https://github.com/etienne-napoleone) for this

## **version:** 0.7.5
- Fix pypi upload script

## **version:** 0.7.4
- Adds support for [ClouDNS](https://www.cloudns.net/): https://github.com/komuw/sewer/pull/122   
   Thanks to [@hbradleyiii](https://github.com/hbradleyiii) for this  
