class AuthProviderInfo():

    def __init__(self,
        name,			# sewer CLI traditional name (usually same as module.py)
        module_name,		# module's sewer-relative (?) dotted-path name
        class_name,		# name of implementation class within module
        req_args,		# tuple of mandantory args to __init__
        opt_args,		# tuple of optional args to __init__
        description		# brief description of the provider
    ):
        self.name = name
        self.module_name = module_name
        self.class_name = class_name
        self.req_args = req_args
        self.opt_args = opt_args
        self.description = description


### FIX ME ### for now, catalog has only zero-dep providers

catalog = (
#    AuthProviderInfo("auroradns", "dns_providers.auroradns", "AuroraDns",
#        ("AURORA_API_KEY", "AURORA_SECRET_KEY"), (),
#        "AuroRa DNS from the dutch hosting provider pcextreme"
#    ),

    AuthProviderInfo("cloudflare", "auth_providers.cloudflare", "CloudFlareDns",
        (), ("CLOUDFLARE_EMAIL", "CLOUDFLARE_API_KEY", "CLOUDFLARE_API_BASE_URL", "CLOUDFLARE_TOKEN"),
        "Cloudflare DNS using either email & key or just a token"
    ),
    AuthProviderInfo("dnspod", "auth_providers.dnspod", "DNSPodDns",
        ("DNSPOD_ID", "DNSPOD_API_KEY"), ("DNSPOD_API_BASE_URL"),
        "DNSPod DNS provider"
    ),
    AuthProviderInfo("duckdns", "auth_providers.duckdns", "DuckDNSDns",
        ("duckdns_token"), ("DUCKDNS_API_BASE_URL"),
        "DuckDNS DNS provider"
    ),
    AuthProviderInfo("powerdns", "auth_provider.powerdns", "PowerDNSDns",
        ("powerdns_api_key", "powerdns_api_url"), (),
        "PowerDNS DNS provider"
    ),
)
