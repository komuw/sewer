import urllib.parse
import requests

from . import common

class DuckDNSDns(common.BaseDns):
    
    dns_provider_name = "duckdns"
    
    def __init__(self, ACME_DNS_API_KEY, ACME_DNS_API_BASE_URL, ACME_DNS_API_USER=""):

        self.ACME_DNS_API_USER = ACME_DNS_API_USER
        self.ACME_DNS_API_KEY = ACME_DNS_API_KEY
        self.HTTP_TIMEOUT = 65  # seconds

        if ACME_DNS_API_BASE_URL[-1] != "/":
            self.ACME_DNS_API_BASE_URL = ACME_DNS_API_BASE_URL + "/"
        else:
            self.ACME_DNS_API_BASE_URL = ACME_DNS_API_BASE_URL
        super(AcmeDnsDns, self).__init__()     

    def create_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("create_dns_record")
        self.logger.info("domain_name: {0} ", domain_name)
        self.logger.info("domain_dns_value: {0} ", domain_dns_value)
        self.logger.info("ACME_DNS_API_BASE_URL: {0} ", self.ACME_DNS_API_BASE_URL)
        self.logger.info("ACME_DNS_API_USER: {0} ", self.ACME_DNS_API_USER)
        self.logger.info("ACME_DNS_API_KEY: {0} ", self.ACME_DNS_API_KEY)

        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")

        url = urllib.parse.urljoin(self.ACME_DNS_API_BASE_URL, "update")

        payload = { "domains": domain_name, "token": self.ACME_DNS_API_KEY , "txt": domain_dns_value}
        update_acmedns_dns_record_response = requests.post(url, params=payload, timeout=self.HTTP_TIMEOUT)
        self.logger.debug("update_acmedns_dns_record_response. status_code={0}. response={1}".format(update_acmedns_dns_record_response.status_code,
                self.log_response(update_acmedns_dns_record_response),))
        if update_acmedns_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError("Error creating acme-dns dns record: status_code={status_code} response={response}".format(status_code=update_acmedns_dns_record_response.status_code,
                    response=self.log_response(update_acmedns_dns_record_response),))
        self.logger.info("create_dns_record_end")   

    def delete_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("delete_dns_record")
        # acme-dns doesn't support this
        self.logger.info("delete_dns_record_success")
