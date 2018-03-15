import os
import logging
import argparse

from . import Client
from . import __version__ as sewer_version


def main():
    """
    Usage:
        1. To get a new certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --dns cloudflare \
        --domain example.com \
        --action run

        2. To renew a certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --account_key /path/to/your/account.key \
        --dns cloudflare \
        --domain example.com \
        --action renew
    """
    # TODO: enable people to specify the location where they want certificate and keys to be stored.
    # currently, we store them in the directory from which sewer is ran
    parser = argparse.ArgumentParser(prog='sewer',
                                     description="""Sewer is a Let's Encrypt(ACME) client.
            Example usage::
            CLOUDFLARE_EMAIL=example@example.com \
            CLOUDFLARE_API_KEY=api-key \
            sewer \
            --dns cloudflare \
            --domain example.com \
            --action run""")
    parser.add_argument(
        "--version",
        action='version',
        version='%(prog)s {version}'.format(version=sewer_version.__version__),
        help="The currently installed sewer version.")
    parser.add_argument(
        "--account_key",
        type=argparse.FileType('r'),
        required=False,
        help="The path to your letsencrypt/acme account key. \
        eg: --account_key /home/myaccount.key")
    parser.add_argument(
        "--dns",
        type=str,
        required=True,
        choices=['cloudflare', 'aurora'],
        help="The name of the dns provider that you want to use.")
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="The domain/subdomain name for which \
        you want to get/renew certificate for. \
        wildcards are also supported \
        eg: --domain example.com")
    parser.add_argument(
        "--alt_domains",
        type=str,
        required=False,
        default=[],
        nargs='*',
        help="A list of alternative domain/subdomain name/s(if any) for which \
        you want to get/renew certificate for. \
        eg: --alt_domains www.example.com blog.example.com")
    parser.add_argument(
        "--bundle_name",
        type=str,
        required=False,
        help="The name to use for certificate \
        certificate key and account key. Default is name of domain.")
    parser.add_argument(
        "--endpoint",
        type=str,
        required=False,
        default='production',
        choices=['production', 'staging'],
        help="Whether to use letsencrypt/acme production/live endpoints \
        or staging endpoints. production endpoints are used by default. \
        eg: --endpoint staging")
    parser.add_argument(
        "--email",
        type=str,
        required=False,
        help="Email to be used for registration and recovery. \
        eg: --email me@example.com")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=['run', 'renew'],
        help="The action that you want to perform. \
        Either run (get a new certificate) or renew (renew a certificate). \
        eg: --action run")
    parser.add_argument(
        "--loglevel",
        type=str,
        required=False,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="The log level to output log messages at. \
        eg: --loglevel DEBUG")

    args = parser.parse_args()

    dns_provider = args.dns
    domain = args.domain
    alt_domains = args.alt_domains
    action = args.action
    account_key = args.account_key
    bundle_name = args.bundle_name
    endpoint = args.endpoint
    email = args.email
    loglevel = args.loglevel

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(loglevel)

    if account_key:
        account_key = account_key.read()
    if bundle_name:
        file_name = bundle_name
    else:
        file_name = '{0}'.format(domain)
    if endpoint == 'staging':
        # TODO: move this to a config.py file.
        # the cli and the client would both read this urls from that config
        # file
        ACME_DIRECTORY_URL = 'https://acme-staging-v02.api.letsencrypt.org/directory'
    else:
        ACME_DIRECTORY_URL = 'https://acme-v02.api.letsencrypt.org/directory'

    if dns_provider == 'cloudflare':
        from . import CloudFlareDns
        try:
            CLOUDFLARE_EMAIL = os.environ['CLOUDFLARE_EMAIL']
            CLOUDFLARE_API_KEY = os.environ['CLOUDFLARE_API_KEY']

            dns_class = CloudFlareDns(
                CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL,
                CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY)
            logger.info(
                'chosen_dns_provider. Using {0} as dns provider.'.format(
                    dns_provider))
        except KeyError as e:
            logger.error(
                "ERROR:: Please supply {0} as an environment variable.".format(
                    str(e)))
            raise

    elif dns_provider == 'aurora':
        from . import AuroraDns
        try:
            AURORA_API_KEY = os.environ['AURORA_API_KEY']
            AURORA_SECRET_KEY = os.environ['AURORA_SECRET_KEY']

            dns_class = AuroraDns(
                AURORA_API_KEY=AURORA_API_KEY,
                AURORA_SECRET_KEY=AURORA_SECRET_KEY)
            logger.info(
                'chosen_dns_provider. Using {0} as dns provider.'.format(
                    dns_provider))
        except KeyError as e:
            logger.error(
                "ERROR:: Please supply {0} as an environment variable.".format(
                    str(e)))
            raise
    else:
        raise ValueError(
            'The dns provider {0} is not recognised.'.format(dns_provider))

    client = Client(
        domain_name=domain,
        dns_class=dns_class,
        domain_alt_names=alt_domains,
        contact_email=email,
        account_key=account_key,
        ACME_DIRECTORY_URL=ACME_DIRECTORY_URL,
        LOG_LEVEL=loglevel)
    certificate_key = client.certificate_key
    account_key = client.account_key

    # write out account_key in current directory
    with open('{0}.account.key'.format(file_name), 'w') as account_file:
        account_file.write(account_key)
    logger.info('account key succesfully written to current directory.')

    if action == 'renew':
        message = 'Certificate Succesfully renewed. The certificate, certificate key and account key have been saved in the current directory'
        certificate = client.renew()
    else:
        message = 'Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory'
        certificate = client.cert()

    # write out certificate and certificate key in current directory
    with open('{0}.crt'.format(file_name), 'w') as certificate_file:
        certificate_file.write(certificate)
    with open('{0}.key'.format(file_name), 'w') as certificate_key_file:
        certificate_key_file.write(certificate_key)

    logger.info("the_end. {0}".format(message))
