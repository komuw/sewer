# DNS service drivers

ACME's dns-01 authorization was sewer's original target.  There are a number
of DNS services supported in-tree, and implementations for other services
are difficult to write only if the service's API is difficult.

## DNS services supported

Currently, these are all _legacy_ drivers, built on the original DNS-only
interface.  That's okay, there's no plan to drop them (just a hope that
interested users will step up to get them updated), but that does mean that
support for some features varies.

| service | driver name | wc+ | alias | prop | notes |
| --- | --- | :-: | :-: | :-: | --- |
| [acme-dns](https://github.com/joohoi/acme-dns) | acmedns | ? | no | no | |
| [Aliyun](https://help.aliyun.com/document_detail/29739.html) | aliyun | ? | no | no | |
| [Aurora](https://www.pcextreme.com/aurora/dns) | aurora | ? | no | no | |
| [Cloudflare](https://www.cloudflare.com/dns) | cloudflare | ? | no | no | patch in #123, needs confirmation? |
| [ClouDNS](https://www.cloudns.net) | cloudns | ? | no | no | test coverage 75% |
| [DNSPod](https://www.dnspod.cn/) | dnspod | ? | no | no |  |
| [DuckDNS](https://www.duckdns.org/) | duckdns | ? | no | no | |
| [Gandi](https://doc.livedns.gandi.net/) | gandi | OK | no | no | wildcard & other fixes in 0.8.3 |
| [Hurricane Electric](https://dns.he.net/) | hurricane | ? | no | no | test coverage 70% |
| [PowerDNS](https://doc.powerdns.com/authoritative/http-api/index.html) | powerdns | NO | no | no | apparently not in 0.8.2; bug #195 |
| [Rackspace](https://www.rackspace.com/cloud/dns) | rackspace | ? | no | no | test coverage 69% | 
| [Route 53 (AWS)](https://aws.amazon.com/route53/) | route53 (1) | OK | no | no | wc+ in 0.8.2; not in CLI |
| Unbound | unbound_ssh | OK | yes | no | Working demonstrator model for local unbound server |

- _wc+_ (wilcard plus) is specifically about a single certificate that has
  at least two registered names: `domain.tld` and `*.domain.tld`.  This
  specific combination has issues with some service providers/s.p.'s
  API/drivers.  So far it's been possible to make it work by changing the
  drivers, but it has to be done one by one.

- _alias_ publishing challenges in a different [sub]domain than the
  identities being authorized.  See [Aliasing](aliasing).

- _prop_ support for the [unpropagated](unpropagated) interface.  Can be
  added to any driver but may only be worthwhile with service API support?

## Add a driver for your DNS service

Most (?) of the DNS drivers came about because someone wanted to use sewer
with their DNS service provider, but there wasn't a driver to use with the
SP yet.  This involvement of sewer and DNS-service users is a practical
necessity, as there is no substitute for being able to test the driver
against the DNS-service, and many such services are for-pay or bundled with
other for-pay services.

sewer's [legacy DNS driver interface](LegacyDNS) (BaseDns in dns_providers/common.py)
is deprecated, although there is no plan for its removal other than
_after they have all migrated to the new interface_.
New DNS drivers should use DNSProviderBase from the start, of course,
and will be placed in sewer/providers/ if added to the project.

    # sketch of simple dns-01 provider, including alias support

    from .. import auth
    from .. import lib

    class Provider(auth.DNSProviderBase):
        def __init__(self, *, my_api_url, my_api_id, my_api_key, **kwargs):
            super().__init__(self, **kwargs)
            self.api_url = my_api_url
            self.api_id = my_api_id
            self.api_key = my_api_key

        def setup(self, challenges):
            for challenge in challenges:
                fqdn = self.target_domain(challenge)
                txt_value = lib.dns_challenge(challenge["key_auth"])
                self.my_api_add_txt(fqdn, txt_value)

        def unpropagated(self, challenges):
            return []  # if service has a propagation check, use it here

        def clear(self, challenges):
            # like setup, but calling my_api_del_txt; may not need txt_value

        def my_api_add_txt(self, fqdn, txt_value):
            # this is where you talk to the DNS service to add a TXT

        def my_api_del_txt(self, fqdn):
            # talk to DNS service to remove TXT

Most of your work is in implementing the two methods (or one method, or
inline code, but inline makes testing without access to the service more
difficult) which actually communicate with the DNS service.  This can be
easy or very difficult, depending on the service provider's API (or lack of
designed API if you have to use a mix of web scraping and HTTP request
generation to operate a mechanism that was designed for interactive use).

The above is bare-bones, not taking advantage of the batching of challenges
which the new-model interface provides - that can be a big win for large-SAN
certificates if you have to grovel the service's API (or web pages) to guide
the construction of your commands to them.  It does show the use of
target_domain to support [DNS aliasing](Aliasing).
