import json
import urlparse

import requests
from structlog import get_logger

from . import common


class CloudFlareDns(common.BaseDns):
    """
    """

    def __init__(
            self,
            CLOUDFLARE_DNS_ZONE_ID,
            CLOUDFLARE_EMAIL,
            CLOUDFLARE_API_KEY,
            CLOUDFLARE_API_BASE_URL='https://api.cloudflare.com/client/v4/'):

        self.CLOUDFLARE_DNS_ZONE_ID = CLOUDFLARE_DNS_ZONE_ID
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        self.dns_provider_name = 'cloudflare'
        self.HTTP_TIMEOUT = 65  # seconds

        if CLOUDFLARE_API_BASE_URL[-1] != '/':
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + '/'
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL

        self.logger = get_logger(__name__).bind(
            dns_provider_name=self.dns_provider_name)

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('create_dns_record')

        # delete any prior existing DNS authorizations that may exist already
        self.delete_dns_record(
            domain_name=domain_name,
            base64_of_acme_keyauthorization=base64_of_acme_keyauthorization)
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
            "name": '_acme-challenge' + '.' + domain_name + '.',
            "content": "{0}".format(base64_of_acme_keyauthorization)
        }
        create_cloudflare_dns_record_response = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=self.HTTP_TIMEOUT)
        self.logger.info(
            'create_cloudflare_dns_record_response',
            status_code=create_cloudflare_dns_record_response.status_code,
            response=create_cloudflare_dns_record_response.json())
        return create_cloudflare_dns_record_response

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('delete_dns_record')

        class MockResponse(object):

            def __init__(self, status_code=200, content='mock-response'):
                self.status_code = status_code
                self.content = content
                super(MockResponse, self).__init__()

            def json(self):
                return {}

        delete_dns_record_response = MockResponse()
        headers = {
            'X-Auth-Email': self.CLOUDFLARE_EMAIL,
            'X-Auth-Key': self.CLOUDFLARE_API_KEY,
            'Content-Type': 'application/json'
        }

        dns_name = '_acme-challenge' + '.' + domain_name
        list_dns_payload = {'type': 'TXT', 'name': dns_name}
        list_dns_url = urlparse.urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            'zones/{0}/dns_records'.format(self.CLOUDFLARE_DNS_ZONE_ID))

        list_dns_response = requests.get(
            list_dns_url,
            params=list_dns_payload,
            headers=headers,
            timeout=self.HTTP_TIMEOUT)

        for i in range(0, len(list_dns_response.json()['result'])):
            dns_record_id = list_dns_response.json()['result'][i]['id']
            url = urlparse.urljoin(self.CLOUDFLARE_API_BASE_URL,
                                   'zones/{0}/dns_records/{1}'.format(
                                       self.CLOUDFLARE_DNS_ZONE_ID,
                                       dns_record_id))
            headers = {
                'X-Auth-Email': self.CLOUDFLARE_EMAIL,
                'X-Auth-Key': self.CLOUDFLARE_API_KEY,
                'Content-Type': 'application/json'
            }
            delete_dns_record_response = requests.delete(
                url, headers=headers, timeout=self.HTTP_TIMEOUT)
            self.logger.info(
                'delete_dns_record_response',
                status_code=delete_dns_record_response.status_code,
                response=delete_dns_record_response.json())
        return delete_dns_record_response
