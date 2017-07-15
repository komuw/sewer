import os
import argparse

from structlog import get_logger

from . import Client


def main():
    """
    Usage:
        1. To get a new certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_DNS_ZONE_ID=some-zone \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --dns cloudflare \
        --domains example.com \
        --action run

        2. To renew a certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_DNS_ZONE_ID=some-zone \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --account_key /path/to/your/account.key \
        --dns cloudflare \
        --domains example.com \
        --action renew
    """
    # TODO: enable people to specify the location where they want certificate and keys to be stored.
    # currently, we store them in the directory from which sewer is ran
    parser = argparse.ArgumentParser(
        prog='sewer', description="Sewer is a Let's Encrypt(ACME) client.")
    parser.add_argument(
        "--account_key",
        type=argparse.FileType('r'),
        required=False,
        help="The path to your letsencrypt/acme account key.")
    parser.add_argument(
        "--dns",
        type=str,
        required=True,
        choices=['cloudflare'],
        help="The name of the dns provider that you want to use.")
    parser.add_argument(
        "--domains",
        type=str,
        required=True,
        help="The domain/subdomain name for which \
        you want to get/renew certificate for.")
    parser.add_argument(
        "--bundle_name",
        type=str,
        required=False,
        help="The name to use for certificate \
        certificate key and account key. Default is value of domains.")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=['run', 'renew'],
        help="The action that you want to perform. \
        Either run (get a new certificate) or renew (renew a certificate).")

    args = parser.parse_args()
    logger = get_logger(__name__)

    dns_provider = args.dns
    domains = args.domains
    action = args.action
    account_key = args.account_key
    bundle_name = args.bundle_name
    if account_key:
        account_key = account_key.read()

    if dns_provider == 'cloudflare':
        from . import CloudFlareDns
        try:
            CLOUDFLARE_EMAIL = os.environ['CLOUDFLARE_EMAIL']
            CLOUDFLARE_API_KEY = os.environ['CLOUDFLARE_API_KEY']
            CLOUDFLARE_DNS_ZONE_ID = os.environ['CLOUDFLARE_DNS_ZONE_ID']

            dns_class = CloudFlareDns(
                CLOUDFLARE_DNS_ZONE_ID=CLOUDFLARE_DNS_ZONE_ID,
                CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL,
                CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY)
            logger.info(
                'chosen_dns_provider',
                message='Using {0} as dns provider.'.format(dns_provider))
        except KeyError as e:
            logger.info("ERROR:: Please supply {0} as an environment variable.".
                        format(str(e)))
    else:
        raise ValueError(
            'The dns provider {0} is not recognised.'.format(dns_provider))

    client = Client(
        domain_name=domains, dns_class=dns_class, account_key=account_key)

    certificate_key = client.certificate_key
    account_key = client.account_key
    if action == 'renew':
        message = 'Certificate Succesfully renewed. The certificate, certificate key and account key have been saved in the current directory'
        certificate = client.renew()
    else:
        message = 'Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory'
        certificate = client.cert()

    if bundle_name:
        file_name = bundle_name
    else:
        file_name = '{0}'.format(domains)

    # write out certificate, certificate key and account key in current directory
    with open('{0}.crt'.format(file_name), 'w') as certificate_file:
        certificate_file.write(certificate)
    with open('{0}.key'.format(file_name), 'w') as certificate_key_file:
        certificate_key_file.write(certificate_key)
    with open('{0}.account.key'.format(file_name), 'w') as account_file:
        account_file.write(account_key)

    logger.info("the_end", message=message)
