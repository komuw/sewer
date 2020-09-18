import argparse, os

from . import client, config, lib

from .catalog import ProviderCatalog
from .crypto import AcmeKey, AcmeAccount, key_type_choices


DEFAULT_KEY_TYPE = "rsa3072"


def setup_parser(catalog):
    """
    return configured ArgumentParser - catalog-driven list of providers
    """

    parser = argparse.ArgumentParser(
        prog="sewer",
        description="Sewer is an ACME client for getting certificates from Let's Encrypt",
        allow_abbrev=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    ### immediate action "options"

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=lib.sewer_meta("version")),
        help="The currently installed sewer version.",
    )
    parser.add_argument(
        "--known_providers",
        action="version",
        version="Known Providers:\n    "
        + "\n    ".join("%s  %s" % (i.name, i.desc) for i in catalog.get_item_list()),
        help="Show a list of the known providers and exit.",
    )

    ### ACME account options

    parser.add_argument(
        "--acct_key",
        "--account_key",
        dest="acct_key_file",
        type=argparse.FileType("rb"),
        help="File to load registered ACME account key from.  Default is to create one.",
    )

    parser.add_argument(
        "--acct_key_type",
        choices=key_type_choices,
        default=DEFAULT_KEY_TYPE,
        help=(
            "Type of acct key to generate if not loaded by --acct_key.  Default %s."
            % DEFAULT_KEY_TYPE
        ),
    ),

    parser.add_argument("--email", help="Email to be used for registration of an ACME account.")

    parser.add_argument(
        "--is_new_acct",
        action="store_true",
        help="Register the key (from --acct_key) rather than assuming it's already registered.",
    ),

    ### certificate options

    parser.add_argument(
        "--cert_key",
        "--certificate_key",
        dest="cert_key_file",
        type=argparse.FileType("rb"),
        help="File to load existing certificate key from.  Default is to create key.",
    )

    parser.add_argument(
        "--cert_key_type",
        choices=[kt for kt in key_type_choices if kt != "secp521r1"],
        default=DEFAULT_KEY_TYPE,
        help=(
            "Type of cert key to generate if not loaded by --cert_key.  Default %s."
            % DEFAULT_KEY_TYPE
        ),
    ),

    parser.add_argument(
        "--domain",
        required=True,
        help="The DNS identity which will be the certificate's Common Name.  May be a wildcard.",
    )

    parser.add_argument(
        "--alt_domains",
        default=[],
        nargs="*",
        help="Optional alternate (SAN) identities to be added to the CN on this certificate.",
    )

    parser.add_argument(
        "--bundle_name",
        help="The basename for the output files.  Default is the CN given by --domain.",
    )

    parser.add_argument(
        "--out_dir",
        default=os.getcwd(),
        help="Directory that stores certificate and keys files; current dir is default.",
    )

    ### challenge provider options

    parser.add_argument(
        "--provider",
        "--dns",
        metavar="<name>",
        dest="provider",
        required=True,
        choices=[i.name for i in catalog.get_item_list()],
        help="Name of the challenge provider to use.  (--dns is OBSOLESCENT; prefer --provider)",
    )
    parser.add_argument(
        "--p_opts", default=[], nargs="*", help="Option(s) to pass to provider, each is key=value"
    )

    ### protocol options

    parser.add_argument(
        "--endpoint",
        default="production",
        choices=["production", "staging"],
        help="Select between Let's Encrypt's endpoints.  Default is production.",
    )
    parser.add_argument(
        "--acme_timeout",
        type=int,
        default=7,
        help="Timeout (maximum wait) for all requests to the ACME service.  Default is 7",
    )

    ### sewer command options

    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The log level to output log messages at. \
        eg: --loglevel DEBUG",
    )
    parser.add_argument(
        "--action",
        choices=["run", "renew"],
        default="none",
        help="[DEPRECATED] The action that you want to perform (has never done anything).",
    )

    return parser


def get_provider(provider_name, provider_kwargs, catalog, logger):
    """
    return class (or callable) that will return the Provider instance to use
    """

    ### TODO ### part of catalog's motivation is to replace all this ad hoc copypasta.

    if provider_name == "cloudflare":
        from .dns_providers.cloudflare import CloudFlareDns

        CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL", None)
        CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY", None)
        CLOUDFLARE_TOKEN = os.environ.get("CLOUDFLARE_TOKEN", None)

        if CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY and not CLOUDFLARE_TOKEN:
            dns_class = CloudFlareDns(
                CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL,
                CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY,
                **provider_kwargs,
            )
        elif CLOUDFLARE_TOKEN and not CLOUDFLARE_EMAIL and not CLOUDFLARE_API_KEY:
            dns_class = CloudFlareDns(CLOUDFLARE_TOKEN=CLOUDFLARE_TOKEN, **provider_kwargs)
        else:
            err = (
                "ERROR:: Please supply either CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY"
                "or CLOUDFLARE_TOKEN as environment variables."
            )
            logger.error(err)
            raise KeyError(err)

    elif provider_name == "aurora":
        from .dns_providers.auroradns import AuroraDns

        try:
            AURORA_API_KEY = os.environ["AURORA_API_KEY"]
            AURORA_SECRET_KEY = os.environ["AURORA_SECRET_KEY"]

            dns_class = AuroraDns(
                AURORA_API_KEY=AURORA_API_KEY,
                AURORA_SECRET_KEY=AURORA_SECRET_KEY,
                **provider_kwargs,
            )
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "acmedns":
        from .dns_providers.acmedns import AcmeDnsDns

        try:
            ACME_DNS_API_USER = os.environ["ACME_DNS_API_USER"]
            ACME_DNS_API_KEY = os.environ["ACME_DNS_API_KEY"]
            ACME_DNS_API_BASE_URL = os.environ["ACME_DNS_API_BASE_URL"]

            dns_class = AcmeDnsDns(
                ACME_DNS_API_USER=ACME_DNS_API_USER,
                ACME_DNS_API_KEY=ACME_DNS_API_KEY,
                ACME_DNS_API_BASE_URL=ACME_DNS_API_BASE_URL,
                **provider_kwargs,
            )
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "aliyun":
        from .dns_providers.aliyundns import AliyunDns

        try:
            aliyun_ak = os.environ["ALIYUN_AK_ID"]
            aliyun_secret = os.environ["ALIYUN_AK_SECRET"]
            aliyun_endpoint = os.environ.get("ALIYUN_ENDPOINT", "cn-beijing")
            dns_class = AliyunDns(aliyun_ak, aliyun_secret, aliyun_endpoint, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "hurricane":
        from .dns_providers.hurricane import HurricaneDns

        try:
            he_username = os.environ["HURRICANE_USERNAME"]
            he_password = os.environ["HURRICANE_PASSWORD"]
            dns_class = HurricaneDns(he_username, he_password, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "rackspace":
        from .dns_providers.rackspace import RackspaceDns

        try:
            RACKSPACE_USERNAME = os.environ["RACKSPACE_USERNAME"]
            RACKSPACE_API_KEY = os.environ["RACKSPACE_API_KEY"]
            dns_class = RackspaceDns(RACKSPACE_USERNAME, RACKSPACE_API_KEY, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "dnspod":
        from .dns_providers.dnspod import DNSPodDns

        try:
            DNSPOD_ID = os.environ["DNSPOD_ID"]
            DNSPOD_API_KEY = os.environ["DNSPOD_API_KEY"]
            dns_class = DNSPodDns(DNSPOD_ID, DNSPOD_API_KEY, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "duckdns":
        from .dns_providers.duckdns import DuckDNSDns

        try:
            duckdns_token = os.environ["DUCKDNS_TOKEN"]
            dns_class = DuckDNSDns(duckdns_token=duckdns_token, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "cloudns":
        from .dns_providers.cloudns import ClouDNSDns

        try:
            dns_class = ClouDNSDns(**provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "powerdns":
        from .dns_providers.powerdns import PowerDNSDns

        try:
            powerdns_api_key = os.environ["POWERDNS_API_KEY"]
            powerdns_api_url = os.environ["POWERDNS_API_URL"]
            dns_class = PowerDNSDns(powerdns_api_key, powerdns_api_url, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "gandi":
        from .dns_providers.gandi import GandiDns

        try:
            gandi_api_key = os.environ["GANDI_API_KEY"]
            dns_class = GandiDns(GANDI_API_KEY=gandi_api_key, **provider_kwargs)
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif provider_name == "unbound_ssh":
        from .dns_providers.unbound_ssh import UnboundSsh

        # check & report, let calling protocol crash it.
        if "ssh_des" not in provider_kwargs:
            logger.error("ERROR: unbound_ssh REQUIRES ssh_des option.")
        dns_class = UnboundSsh(**provider_kwargs)  # pylint: disable=E1125

    elif provider_name == "route53":
        raise ValueError("route53 driver can only be used programmatically at this time, sorry")

    else:
        raise ValueError("The dns provider {0} is not recognised.".format(provider_name))

    logger.info("Using %s as registered provider.", provider_name)
    return dns_class


def main():
    "See docs/sewer-cli.md for docs & examples"

    catalog = ProviderCatalog()

    parser = setup_parser(catalog)
    args = parser.parse_args()

    loglevel = args.loglevel
    logger = lib.create_logger(None, loglevel)

    provider_name = args.provider
    domain = args.domain
    alt_domains = args.alt_domains
    if args.action != "none":
        logger.warning("DEPRECATION WARNING: --action option is obsolete and will be dropped soon")
    bundle_name = args.bundle_name
    endpoint = args.endpoint
    email = args.email
    out_dir = args.out_dir

    ### FIX ME ### to keep special options --domain_alias & --prop-*, or use -p_opts instead?

    provider_kwargs = {}

    for p in args.p_opts:
        parts = p.split("=")
        if len(parts) == 2:
            provider_kwargs[parts[0]] = parts[1]

    # Make sure the output dir user specified is writable
    if not os.access(out_dir, os.W_OK):
        raise OSError("The dir '{0}' is not writable".format(out_dir))

    if args.acct_key_file:
        account = AcmeAccount.from_pem(args.acct_key_file.read())
        is_new_acct = args.is_new_acct
    else:
        account = AcmeAccount.create(args.acct_key_type)
        is_new_acct = True

    if args.cert_key_file:
        cert_key = AcmeKey.from_pem(args.cert_key.read())
    else:
        cert_key = AcmeKey.create(args.cert_key_type)

    if bundle_name:
        file_name = bundle_name
    else:
        file_name = "{0}".format(domain)

    if endpoint == "staging":
        ACME_DIRECTORY_URL = config.ACME_DIRECTORY_URL_STAGING
    else:
        ACME_DIRECTORY_URL = config.ACME_DIRECTORY_URL_PRODUCTION

    dns_class = get_provider(provider_name, provider_kwargs, catalog, logger)

    acme_client = client.Client(
        provider=dns_class,
        domain_name=domain,
        domain_alt_names=alt_domains,
        contact_email=email,
        account=account,
        is_new_acct=is_new_acct,
        cert_key=cert_key,
        ACME_DIRECTORY_URL=ACME_DIRECTORY_URL,
        LOG_LEVEL=loglevel,
        ACME_REQUEST_TIMEOUT=args.acme_timeout,
    )

    # prepare file path
    account_key_file_path = os.path.join(out_dir, "{0}.account.key".format(file_name))
    crt_file_path = os.path.join(out_dir, "{0}.crt".format(file_name))
    crt_key_file_path = os.path.join(out_dir, "{0}.key".format(file_name))

    # write out account_key in out_dir directory
    account.write_pem(account_key_file_path)
    logger.info("account key succesfully written to {0}.".format(account_key_file_path))

    certificate = acme_client.get_certificate()

    # write out certificate and certificate key in out_dir directory
    with open(crt_file_path, "w") as certificate_file:
        certificate_file.write(certificate)
    logger.info("certificate succesfully written to {0}.".format(crt_file_path))

    cert_key.write_pem(crt_key_file_path)
    logger.info("certificate key succesfully written to {0}.".format(crt_key_file_path))
