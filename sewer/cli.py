import os
import argparse

from structlog import get_logger

from . import Client


def main():
    """
    Usage:
        CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL \
        CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY \
        CLOUDFLARE_DNS_ZONE_ID=CLOUDFLARE_DNS_ZONE_ID \
        GET_NONCE_URL=GET_NONCE_URL \
        ACME_CERTIFICATE_AUTHORITY_URL=ACME_CERTIFICATE_AUTHORITY_URL \
        ACME_CERTIFICATE_AUTHORITY_TOS=ACME_CERTIFICATE_AUTHORITY_TOS \
        ACME_CERTIFICATE_AUTHORITY_CHAIN=ACME_CERTIFICATE_AUTHORITY_CHAIN \
        CLOUDFLARE_API_BASE_URL=CLOUDFLARE_API_BASE_URL \
        sewer --account_key="/path/" --dns="cloudflare" --domains="yo.com" renew/run
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

    account_key = args.account_key
    dns_proviser = args.dns
    domains = args.domains
    action = args.action
    try:
        CLOUDFLARE_EMAIL = os.environ['CLOUDFLARE_EMAIL']
        CLOUDFLARE_API_KEY = os.environ['CLOUDFLARE_API_KEY']
        CLOUDFLARE_DNS_ZONE_ID = os.environ['CLOUDFLARE_DNS_ZONE_ID']
    except KeyError as e:
        logger.info("ERROR:: Please supply {0} as an environment variable.".
                    format(str(e)))

    print "\n\n"
    print "args:", args
