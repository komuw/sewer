import urllib.parse
import requests

from . import common

class DuckDNSDns(common.BaseDns):
    
    dns_provider_name = "duckdns"
    
    def __init__(self, duckdns_token, DUCKDNS_API_BASE_URL='https://www.duckdns.org'):

        self.duckdns_token = duckdns_token
        self.HTTP_TIMEOUT = 65  # seconds

        if DUCKDNS_API_BASE_URL[-1] != "/":
            self.DUCKDNS_API_BASE_URL = DUCKDNS_API_BASE_URL + "/"
        else:
            self.DUCKDNS_API_BASE_URL = DUCKDNS_API_BASE_URL
        super(DuckDNSDns, self).__init__(LOG_LEVEL="DEBUG")     

    def create_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("create_dns_record")

        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")

        url = urllib.parse.urljoin(self.DUCKDNS_API_BASE_URL, "update")

        payload = { "domains": domain_name, "token": self.duckdns_token , "txt": domain_dns_value}
        update_duckdns_dns_record_response = requests.get(url, params=payload, timeout=self.HTTP_TIMEOUT)
        self.logger.debug("update_duckdns_dns_record_response. status_code={0}. response={1}".format(update_duckdns_dns_record_response.status_code,
                self.log_response(update_duckdns_dns_record_response),))
        if update_duckdns_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to DuckDNS
            # server
            raise ValueError("Error creating DuckDNS dns record: status_code={status_code} response={response}".format(status_code=update_acmedns_dns_record_response.status_code,
                    response=self.log_response(update_duckdns_dns_record_response),))
        self.logger.info("create_dns_record_end")   

    def delete_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("delete_dns_record")
        domain_name = domain_name.lstrip("*.")

        url = urllib.parse.urljoin(self.DUCKDNS_API_BASE_URL, "update")

        payload = { "domains": domain_name, "token": self.duckdns_token , "txt": "removed", "clear": "true"}
        update_duckdns_dns_record_response = requests.get(url, params=payload, timeout=self.HTTP_TIMEOUT)
        self.logger.debug("update_duckdns_dns_record_response. status_code={0}. response={1}".format(update_duckdns_dns_record_response.status_code,
                self.log_response(update_duckdns_dns_record_response),))
        if update_duckdns_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to DuckDNS
            # server
            raise ValueError("Error removing DuckDNS dns record: status_code={status_code} response={response}".format(status_code=update_acmedns_dns_record_response.status_code,
                    response=self.log_response(update_duckdns_dns_record_response),))
        self.logger.info("delete_dns_record_success")
