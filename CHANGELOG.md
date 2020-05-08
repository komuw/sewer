## `sewer` changelog:
most recent version is listed first.   

## **unreleased:** heading for 0.9
- README and other docs need updating!
- mypy & python version compatibility verification?
- at least a couple sample http-01 challenge providers & dns-01 (new or ported to new API)
- **WIP** refactor provider API; distinction between dns and http providers deprecated
### This might be a good point for 0.9-alpha - new features but not complete
- support current RFC8555 protocol (LE staging current, production will require in Nov)
- collect shared (internal) functions into lib.py
- use unitest.mock rather than external module
- client no longer prepends`*.` to wildcards; remove spotty code in providers to strip it
- added support for non-dns (http-01 challenge) provider [API change, more ahead]
- added DNS providers powerdns and gandi
- begin addition of annotations, mostly opportunistically; may be[come] incompat w/py < 3.5

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
