# sewer's DNS service support

ACME's dns-01 authorization was sewer's original target.
There are a number of DNS services supported in-tree,
and implementations for other services are difficult to write only if the
service's API is difficult.

## DNS services supported

- [acme-dns](https://github.com/joohoi/acme-dns)
- [Aliyun](https://help.aliyun.com/document_detail/29739.html)
- [Aurora](https://www.pcextreme.com/aurora/dns)
- [AWS Route 53](https://aws.amazon.com/route53/)
- [Cloudflare](https://www.cloudflare.com/dns)
- [ClouDNS](https://www.cloudns.net)
- [DNSPod](https://www.dnspod.cn/)
- [DuckDNS](https://www.duckdns.org/)
- [Gandi](https://doc.livedns.gandi.net/)
- [Hurricane Electric DNS](https://dns.he.net/)
- [PowerDNS](https://doc.powerdns.com/authoritative/http-api/index.html)
- [Rackspace](https://www.rackspace.com/cloud/dns)

## Add a driver for your DNS service

sewer's [legacy DNS driver interface](LegacyDNS) (BaseDns in dns_providers/common.py)
is deprecated, although there is no schedule for its removal at this time.
These legacy drivers should be migrated to the new DNSProviderBase (in
auth.py) when practical.  New DNS drivers should use DNSProviderBase from
the start, of course, and will be placed in sewer/providers/ if added to the
project.

    # sketch of dns-01 provider, including alias support

    from ..auth import DNSProviderBase
    from ..lib import dns_challenge

    class Provider(DNSProviderBase):
        def __init__(self, *, my_api_url, my_api_id, my_api_key, **kwargs):
	    super().__init__(self, **kwargs)
            self.api_url = my_api_url
            self.api_id = my_api_id
            self.api_key = my_api_key

        def setup(self, challenges):
	    for challenge in challenges:
                fqdn = self.target_domain(challenge)
                txt_value = dns_challenge(challenge["key_auth"])
                self.my_api_add_txt(fqdn, txt_value)

        def unpropagated(self, challenges):
            return []  # if service has a propagation check, use it here

        def clear(self, challenges):
            # like setup, but calling my_api_del_txt; may not need txt_value

        def my_api_add_txt(self, fqdn, txt_value):
            # this is where you talk to the DNS service to add a TXT

        def my_api_del_txt(self, fqdn):
            # talk to DNS service to remove TXT

Most of your work is in implementing the two methods which actually
communicate with the DNS service.  This can be easy or very difficult,
depending on the service provider's API (or lack of designed API if you have
to use a mix of web scraping and HTTP request generation to operate a
mechanism that was designed for interactive use).

The above is bare-bones, not taking advantage of the batching of challenges
which the new-model interface provides - that can be huge if you have to
grovel the service's API (or web pages) to guide the construction of your
commands to them.  It does show the use of target_domain to support
[DNS aliasing](Aliasing).

## Legacy DNS drivers vs. $FEATURES

Three recent features that have varying support in the Legacy drivers.

_wildcard_ is support for the special case where both *.domain.tld and
domin.tld are requested in the same certificate.  The potential problem and
the fix are service-specific.

_alias_ is the new (0.8.3) --alias_domain feature, which none of the legacy
drivers initially supported.

_prop_ is support for the "check & wait" propagation wait (new in 0.8.2),
which none of the legacy providers initially supported.

| driver name | wildcard | alias | prop | notes |
| --- | :-: | :-: | :-: | ---|
| acmedns | ? | no | no | |
| aliyun | ? | no | no | |
| aurora | ? | no | no | |
| cloudns | ? | no | no | |
| cloudflare | ? | no | no | wc patch exists, reported to work |
| dnspod | ? | no | no | |
| duckdns | ? | no | no | |
| hurricane | ? | no | no | |
| powerdns | ? | no | no | |
| rackspace | ? | no | no | | 
| route53 | ok | no | no | wc +1 from pre-0.8.2 |

_updated pre-0.8.3 release_
