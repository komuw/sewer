## sewer's DNS service support

ACME's dns-01 authorization was sewer's original target.
There are a number of DNS services supported in-tree,
and implementations for other services are difficult to write only if the
service's API is difficult.

### DNS services supported

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
- [unbound_ssh]

### Add a driver for your DNS service

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

    # sketch of dns-01 provider, including alias support [which is NOT in 0.8.2]

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

### Legacy DNS drivers vs. $FEATURES

Three features that have varying support in the Legacy drivers.

| driver name | wildcard | alias | prop | notes |
| --- | :-: | :-: | :-: | ---|
| acmedns | ? | no | no | |
| aliyun | ? | no | no | |
| aurora | ? | no | no | |
| cloudns | ? | no | no | test coverage 75% |
| cloudflare | ? | no | no | patch in #123, needs confirmation? |
| dnspod | ? | no | no | |
| duckdns | ? | no | no | |
| gandi | OK | no | no | wildcard & other fixes in 0.8.3 |
| hurricane | ? | no | no | test coverage 70% |
| powerdns | NO | no | no | apparently not in 0.8.2; bug #195 |
| rackspace | ? | no | no | test coverage 69% | 
| route53 (1) | OK | no | no | wildcard since pre-0.8.2 |
| unbound_ssh | OK | yes | no | Working demonstrator model |

> (1) route53 was never setup to be used from `sewer-cli`.  That will change,
maybe for 0.8.3, but does anyone care?  No complaints have been heard...

_wildcard_ is NOT the older issue - since 0.8.2, all drivers should be able
to support creating certificates for simple `*.domain.tld` requests.
There is a deeper problem when one wants a wildcard that _also_ covers plain
`domain.tld`, which is sometimes desired.
Because of the way ACME and DNS work, such a certificate must post two
different challenge responses on the same DNS name (domain.tld).
DNS inherently supports this, and all the DNS services that have been
examined so far support it, but their APIs don't always make it easy.
And that's why some drivers cannot yet handle these _wildcard-plus_
requests.  _I'm sure some of those "unknowns" are "OK", but I can't find
evidence at this time._

_alias_ is the new (0.8.3) `--p_opts alias=...` feature, which none of the legacy
drivers initially supported.

_prop_ is support for the "check & wait" propagation wait (engine support in 0.8.2),
which none of the legacy providers support (yet?).  Note that `prop_delay`,
although passed through the driver, is working without driver support aside
from **kwargs.  The other `prop_*` parameters are what this column reports.

_updated pre-0.8.3 release_
