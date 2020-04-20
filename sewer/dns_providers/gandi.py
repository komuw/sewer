import os
import requests

from . import common


class GandiDns(common.BaseDns):
    """
    """

    dns_provider_name = "gandi"

    def __init__(
        self,
        GANDI_API_KEY=None,
        GANDI_API_BASE_URL="https://dns.api.gandi.net/api/v5/",
        DEFAULT_TTL=10800,
        requests_lib=requests,
    ):
        self.GANDI_API_KEY = GANDI_API_KEY
        self.HTTP_TIMEOUT = 65  # seconds
        self.RECORD_TTL = DEFAULT_TTL
        self.requests = requests_lib

        if GANDI_API_BASE_URL[-1] != "/":
            self.GANDI_API_BASE_URL = GANDI_API_BASE_URL + "/"
        else:
            self.GANDI_API_BASE_URL = GANDI_API_BASE_URL

        # pass an API key
        if not GANDI_API_KEY:
            raise ValueError("Error initializing Gandi DNS adapter. Pass an API key.")

        self.GET_HEADERS = {"X-Api-Key": self.GANDI_API_KEY}
        self.POST_HEADERS = {"X-Api-Key": self.GANDI_API_KEY, "Content-Type": "application/json"}

        super(GandiDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        self.delete_record(domain_name, idempotent=True)
        [subdomain, base_domain] = GandiDns.split_domain(domain_name)
        zone_records_href = self.get_zone_records_href(base_domain)

        request_body = {
            "rrset_type": "TXT",
            "rrset_ttl": self.RECORD_TTL,
            "rrset_name": GandiDns.subdomain_to_challenge_domain(subdomain),
            "rrset_values": [domain_dns_value],
        }

        create_record_resp = self.requests.post(
            zone_records_href, headers=self.POST_HEADERS, json=request_body
        )
        if not create_record_resp.status_code < 300:
            raise RuntimeError("createRecord failed")

    def delete_dns_record(self, domain_name, domain_dns_value):
        self.delete_record(domain_name)

    def delete_record(self, domain_name, idempotent=False):
        def get_subdomain_record(subdomain, all_records):
            subdomain_records = list(
                filter(lambda rec: rec["rrset_name"] == subdomain, all_records)
            )
            if not len(subdomain_records) == 1:
                if idempotent:
                    return None
                else:
                    raise RuntimeError("there is not exactly one record for domain: " + domain_name)

            return subdomain_records[0]

        [subdomain, base_domain] = GandiDns.split_domain(domain_name)
        zone_records_href = self.get_zone_records_href(base_domain)
        all_records = self.get_all_zone_records(zone_records_href)
        subdomain_record = get_subdomain_record(
            GandiDns.subdomain_to_challenge_domain(subdomain), all_records
        )

        if subdomain_record:
            del_record_resp = self.requests.delete(
                subdomain_record["rrset_href"], headers=self.GET_HEADERS
            )
            if not del_record_resp.status_code < 300:
                raise RuntimeError("deleteRecord failed")

    def get_zone_records_href(self, base_domain):
        domain_resp = self.requests.get(
            os.path.join(self.GANDI_API_BASE_URL, "domains", base_domain), headers=self.GET_HEADERS
        )

        if not domain_resp.status_code < 300:
            raise RuntimeError("getZoneHref failed")

        domain_info = domain_resp.json()
        return domain_info["zone_records_href"]

    def get_all_zone_records(self, zone_records_href):
        all_records_resp = self.requests.get(zone_records_href, headers=self.GET_HEADERS)
        if not all_records_resp.status_code < 300:
            raise RuntimeError("getAllZoneRecords failed")

        all_records = all_records_resp.json()
        return all_records

    @staticmethod
    def split_domain(domain_name):
        def has_second_level_domain(split_domains):
            return len(split_domains) >= 2

        split_domains = domain_name.split(".")
        if not has_second_level_domain(split_domains):
            raise RuntimeError(
                "domain: " + str(domain_name) + "does not have a second level domain"
            )

        separator = "."
        base_domain = separator.join(split_domains[-2:])
        subdomain = separator.join(split_domains[0:-2])
        if not subdomain:
            subdomain = "@"

        return [subdomain, base_domain]

    @staticmethod
    def subdomain_to_challenge_domain(subdomain):
        return "_acme-challenge" + "." + subdomain
