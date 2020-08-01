## `sewer` changelog:
most recent version is listed first.   

## **version:** 0.8.3
STILL TO DO:
- tests for unbound_ssh?!


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
  could be useful to someone, maybe.

Internals:
- added [catalog.py](catalog) to manage provider catalogs; includes
  get_provider(name) method to replace `import ......{name.}ClassName`
- replace __version__.py with sewer.json; setup.py converted; add sewer_about()
  in lib.py; cli.py converted; client.py converted
- added catalog.json defining known drivers and their interfaces; also
  information about dependencies for setup.py
- added `**kwargs` to all legacy providers to allow new options that are
  handled in a parent class to pass through (for `alias`, `prop_delay`, etc.)
- removed imports that were in `sewer/__init__` and
  `sewer/dns_providers/__init__`; fixed all uses in cli.py and tests.
- began cleanup/refactor of cli.py (there will be more to come and/or a new,
  more config driven, alternative command (0.9?))
- added `__main__.py` to support `python3 -m sewer` invocation of sewer-cli
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
