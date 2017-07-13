import os
import argparse

from structlog import get_logger

from . import Client


def main():
    """
    Usage:
        CLOUDFLARE_EMAIL=komuw05@gmail.com \
        CLOUDFLARE_DNS_ZONE_ID=zone \
        CLOUDFLARE_API_KEY=key \
        sewer \
        --account_key /tmp/account_key.key \
        --dns cloudflare \
        --domains yo.com \
        --action run 
    """
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
        help="The domain name for which you want to get/renew certificate for.")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=['run', 'renew'],
        help="The action that you want to. \
        Either run(get a new certificate) or renew(renew a certificate).")

    args = parser.parse_args()
    logger = get_logger(__name__)

    dns_provider = args.dns
    domains = args.domains
    action = args.action
    account_key = args.account_key
    if account_key:
        account_key = account_key.read()
    try:
        CLOUDFLARE_EMAIL = os.environ['CLOUDFLARE_EMAIL']
        CLOUDFLARE_API_KEY = os.environ['CLOUDFLARE_API_KEY']
        CLOUDFLARE_DNS_ZONE_ID = os.environ['CLOUDFLARE_DNS_ZONE_ID']
    except KeyError as e:
        logger.info("ERROR:: Please supply {0} as an environment variable.".
                    format(str(e)))

    client = Client(
        domain_name=domains,
        CLOUDFLARE_DNS_ZONE_ID=CLOUDFLARE_DNS_ZONE_ID,
        CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL,
        CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY,
        account_key=account_key)

    certificate_key = client.certificate_key
    account_key = client.account_key
    # if action == 'renew':
    #     certificate = client.renew()
    # else:
    #     certificate = client.cert()

    print "\n\n"
    print "certificate_key:", certificate_key
    print "\n\n"
    print "account_key:", account_key
    print "\n\n"
    print "certificate:", 'certificate'
