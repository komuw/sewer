import time
import json
import base64
import hashlib
import binascii
import urlparse

import requests
import OpenSSL
import Crypto.PublicKey.RSA
from structlog import get_logger


class ACMEclient(object):
    """
    todo: improve documentation.

    usage:
        client = ACMEclient(domain_name='example.com',
                            CLOUDFLARE_DNS_ZONE_ID='random',
                            CLOUDFLARE_EMAIL='example@example.com',
                            CLOUDFLARE_API_KEY='nsa-grade-api-key')
        acme_register_response = client.acme_register()
        dns_token, dns_challenge_url = client.get_challenge()
        acme_keyauthorization, base64_of_acme_keyauthorization = client.get_keyauthorization(dns_token)
        create_cloudflare_dns_record_response = client.create_cloudflare_dns_record(self, base64_of_acme_keyauthorization)
        notify_acme_challenge_set_response = client.notify_acme_challenge_set(acme_keyauthorization, dns_challenge_url)
        dns_record_id = create_cloudflare_dns_record_response.json()['result']['id']
        check_challenge_status_response = client.check_challenge_status(dns_record_id, dns_challenge_url)

    todo:
        - reduce number of steps taken to get certificates.
        - handle exceptions
    """

    def __init__(
            self,
            domain_name,
            CLOUDFLARE_DNS_ZONE_ID,
            CLOUDFLARE_EMAIL,
            CLOUDFLARE_API_KEY,
            account_key=None,
            bits=2048,
            digest='sha256',
            ACME_REQUEST_TIMEOUT=65,
            ACME_CHALLENGE_WAIT_PERIOD=4,
            GET_NONCE_URL="https://acme-staging.api.letsencrypt.org/directory",
            ACME_CERTIFICATE_AUTHORITY_URL="https://acme-staging.api.letsencrypt.org",
            ACME_CERTIFICATE_AUTHORITY_TOS='https://letsencrypt.org/documents/LE-SA-v1.1.1-August-1-2016.pdf',
            ACME_CERTIFICATE_AUTHORITY_CHAIN='https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem',
            CLOUDFLARE_API_BASE_URL='https://api.cloudflare.com/client/v4/'):

        self.logger = get_logger(__name__).bind(
            client_name=self.__class__.__name__)

        self.domain_name = domain_name
        self.CLOUDFLARE_DNS_ZONE_ID = CLOUDFLARE_DNS_ZONE_ID
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.bits = bits
        self.digest = digest
        self.ACME_REQUEST_TIMEOUT = ACME_REQUEST_TIMEOUT
        self.ACME_CHALLENGE_WAIT_PERIOD = ACME_CHALLENGE_WAIT_PERIOD
        self.GET_NONCE_URL = GET_NONCE_URL
        self.ACME_CERTIFICATE_AUTHORITY_URL = ACME_CERTIFICATE_AUTHORITY_URL
        self.ACME_CERTIFICATE_AUTHORITY_TOS = ACME_CERTIFICATE_AUTHORITY_TOS
        self.ACME_CERTIFICATE_AUTHORITY_CHAIN = ACME_CERTIFICATE_AUTHORITY_CHAIN

        if not account_key:
            self.account_key = self.create_account_key()
        else:
            self.account_key = account_key

        if CLOUDFLARE_API_BASE_URL[-1] != '/':
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + '/'
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL

        self.logger = self.logger.bind(
            client_name=self.__class__.__name__,
            domain_name=self.domain_name,
            ACME_CERTIFICATE_AUTHORITY_URL=self.ACME_CERTIFICATE_AUTHORITY_URL,
            CLOUDFLARE_API_BASE_URL=self.CLOUDFLARE_API_BASE_URL)

        # for production/live use:
        # self.GET_NONCE_URL = "https://acme-v01.api.letsencrypt.org/directory"
        # self.ACME_CERTIFICATE_AUTHORITY_URL = "https://acme-v01.api.letsencrypt.org"

    def create_account_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        self.logger.info('create_account_key')
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def calculate_safe_base64(self, un_encoded_data):
        return base64.urlsafe_b64encode(un_encoded_data).decode('utf8').rstrip(
            '=')

    def sign_message(self, message):
        self.logger.info('sign_message')
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                            self.account_key)
        return OpenSSL.crypto.sign(pk, message.encode('utf8'), self.digest)

    def get_acme_header(self):
        self.logger.info('get_acme_header')
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                            self.account_key)
        pk_asn1 = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_ASN1,
                                                 pk)
        k = Crypto.PublicKey.RSA.importKey(pk_asn1)

        # private key public exponent in hex format
        exponent = "{0:x}".format(k.e)
        exponent = "0{0}".format(exponent) if len(exponent) % 2 else exponent
        # private key modulus in hex format
        modulus = "{0:x}".format(k.n)
        header = {
            "alg": "RS256",
            "jwk": {
                "e":
                self.calculate_safe_base64(
                    binascii.unhexlify(exponent.encode('utf8'))),
                "kty":
                "RSA",
                "n":
                self.calculate_safe_base64(
                    binascii.unhexlify(modulus.encode('utf8')))
            }
        }
        return header

    def make_signed_acme_request(self, url, payload):
        self.logger.info('make_signed_acme_request')
        payload64 = self.calculate_safe_base64(
            json.dumps(payload).encode('utf8'))
        protected = self.get_acme_header(self.account_key)

        response = requests.get(
            self.GET_NONCE_URL, timeout=self.ACME_REQUEST_TIMEOUT)
        nonce = response.headers['Replay-Nonce']
        protected["nonce"] = nonce

        protected64 = self.calculate_safe_base64(
            json.dumps(protected).encode('utf8'))
        signature = self.sign_message(self.account_key, "{0}.{1}".format(
            protected64, payload64))
        data = json.dumps({
            "protected": protected64,
            "payload": payload64,
            "signature": self.calculate_safe_base64(signature)
        })
        response = requests.post(
            url, data=data.encode('utf8'), timeout=self.ACME_REQUEST_TIMEOUT)
        return response

    def acme_register(self):
        self.logger.info('acme_register')
        payload = {
            "resource": "new-reg",
            "agreement": self.ACME_CERTIFICATE_AUTHORITY_TOS
        }
        url = urlparse.urljoin(self.ACME_CERTIFICATE_AUTHORITY_URL,
                               '/acme/new-reg')
        acme_register_response = self.make_signed_acme_request(
            url=url, payload=payload)
        return acme_register_response

    def get_challenge(self):
        self.logger.info('get_challenge')
        payload = {
            "resource": "new-authz",
            "identifier": {
                "type": "dns",
                "value": self.domain_name
            }
        }
        url = urlparse.urljoin(self.ACME_CERTIFICATE_AUTHORITY_URL,
                               '/acme/new-authz')
        challenge_response = self.make_signed_acme_request(
            url=url, payload=payload)

        for i in challenge_response.json()['challenges']:
            if i['type'] == 'dns-01':
                dns_challenge = i
        dns_token = dns_challenge['token']
        dns_challenge_url = dns_challenge['uri']

        return dns_token, dns_challenge_url

    def get_keyauthorization(self, dns_token):
        self.logger.info('get_keyauthorization')
        acme_header_jwk_json = json.dumps(
            self.get_acme_header()['jwk'],
            sort_keys=True,
            separators=(',', ':'))
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode('utf8')).digest())
        acme_keyauthorization = "{0}.{1}".format(dns_token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest())

        return acme_keyauthorization, base64_of_acme_keyauthorization

    def create_cloudflare_dns_record(self, base64_of_acme_keyauthorization):
        self.logger.info('create_cloudflare_dns_record')
        url = urlparse.urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            'zones/{0}/dns_records'.format(self.CLOUDFLARE_DNS_ZONE_ID))
        headers = {
            'X-Auth-Email': self.CLOUDFLARE_EMAIL,
            'X-Auth-Key': self.CLOUDFLARE_API_KEY,
            'Content-Type': 'application/json'
        }
        body = {
            "type": "TXT",
            "name": '_acme-challenge' + '.' + self.domain_name,
            "content": "{0}".format(base64_of_acme_keyauthorization)
        }
        create_cloudflare_dns_record_response = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=self.ACME_REQUEST_TIMEOUT)
        return create_cloudflare_dns_record_response

    def notify_acme_challenge_set(self, acme_keyauthorization,
                                  dns_challenge_url):
        self.logger.info('notify_acme_challenge_set')
        payload = {
            "resource": "challenge",
            "keyAuthorization": "{0}".format(acme_keyauthorization)
        }
        notify_acme_challenge_set_response = self.make_signed_acme_request(
            dns_challenge_url, payload, self.account_key)
        return notify_acme_challenge_set_response

    def check_challenge_status(self, dns_record_id, dns_challenge_url):
        self.logger.info('check_challenge')
        time.sleep(self.ACME_CHALLENGE_WAIT_PERIOD)
        while True:
            try:
                check_challenge_status_response = requests.get(
                    dns_challenge_url, timeout=self.ACME_REQUEST_TIMEOUT)
                challenge_status = check_challenge_status_response.json()[
                    'status']
            except Exception as e:
                self.logger.info('check_challenge', error=str(e))
                break
            if challenge_status == "pending":
                time.sleep(self.ACME_CHALLENGE_WAIT_PERIOD)
            elif challenge_status == "valid":
                self.delete_cloudflare_dns_record(dns_record_id=dns_record_id)
                break
        return check_challenge_status_response

    def delete_cloudflare_dns_record(self, dns_record_id):
        self.logger.info('delete_cloudflare_dns_record')
        url = urlparse.urljoin(self.CLOUDFLARE_API_BASE_URL,
                               'zones/{0}/dns_records/{1}'.format(
                                   self.CLOUDFLARE_DNS_ZONE_ID, dns_record_id))
        headers = {
            'X-Auth-Email': self.CLOUDFLARE_EMAIL,
            'X-Auth-Key': self.CLOUDFLARE_API_KEY,
            'Content-Type': 'application/json'
        }
        response = requests.delete(
            url, headers=headers, timeout=self.ACME_REQUEST_TIMEOUT)
        return response
