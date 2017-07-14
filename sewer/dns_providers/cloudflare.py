import json
import urlparse

import requests

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
        self.HTTP_TIMEOUT = 65 # seconds

        if CLOUDFLARE_API_BASE_URL[-1] != '/':
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + '/'
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
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
            "name": '_acme-challenge' + '.' + domain_name,
            "content": "{0}".format(base64_of_acme_keyauthorization)
        }
        create_cloudflare_dns_record_response = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=self.HTTP_TIMEOUT)
        return create_cloudflare_dns_record_response

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        headers = {
            'X-Auth-Email': self.CLOUDFLARE_EMAIL,
            'X-Auth-Key': self.CLOUDFLARE_API_KEY,
            'Content-Type': 'application/json'
        }
        list_dns_payload = {'type': 'TXT', 'name': domain_name}
        list_dns_url = urlparse.urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            'zones/{0}/dns_records'.format(self.CLOUDFLARE_DNS_ZONE_ID))

        list_dns_response = requests.get(
            list_dns_url,
            params=list_dns_payload,
            headers=headers,
            timeout=self.HTTP_TIMEOUT)

        print "list_dns_response status:", list_dns_response
        print "\n\n"
        print "list_dns_response json", list_dns_response.json()

        url = urlparse.urljoin(self.CLOUDFLARE_API_BASE_URL,
                               'zones/{0}/dns_records/{1}'.format(
                                   self.CLOUDFLARE_DNS_ZONE_ID, dns_record_id))
        headers = {
            'X-Auth-Email': self.CLOUDFLARE_EMAIL,
            'X-Auth-Key': self.CLOUDFLARE_API_KEY,
            'Content-Type': 'application/json'
        }
        response = requests.delete(
            url, headers=headers, timeout=self.HTTP_TIMEOUT)
        return response