import json
import requests

from . import common


class PowerDNSDns(common.BaseDns):
    """
    For PowerDNS, all subdomains for a given domain live under the apex zone `zone_id`.
    For example, if you want a cert for domain.tld and www.domain.tld, you need
    to create two DNS records:
    1) `acme-challenge.domain.tld. IN TXT`
    2) `acme-challenge.www.domain.tld. IN TXT`

    However, both of these records must be created under `/servers/{server_id}/zones/{zone_id}`,
    where `zone_id` is the apex domain (`domain.tld`)

    So, we must be smart about stripping out subdomains as part of the URL passed
    to `requests.patch`, but must maintain the FQDN in the `name` field of the `payload`.
    """

    dns_provider_name = "powerdns"

    def __init__(self, powerdns_api_key, powerdns_api_url):
        self.powerdns_api_key = powerdns_api_key
        self.powerdns_api_url = powerdns_api_url
        super(PowerDNSDns, self).__init__()

    def validate_powerdns_zone(self, domain_name):
        """
        Walk `domain_name` backwards, trying to find the apex domain.
        E.g.: For `fu.bar.baz.domain.com`, `response.status_code` will only be
        `200` for `domain.com`
        """
        d = "."
        count = domain_name.count(d)

        while True:
            url = self.powerdns_api_url + "/" + domain_name
            response = requests.get(url, headers={"X-API-Key": self.powerdns_api_key})

            if response.status_code == 200:
                return domain_name
            elif count <= 0:
                raise ValueError(
                    f"Could not determine apex domain: (count: {count}, domain_name: {domain_name})"
                )
            else:
                split = domain_name.split(d)
                split.pop(0)
                domain_name = d.join(split)
                count -= 1

    def _common_dns_record(self, domain_name, domain_dns_value, changetype):
        if changetype not in ("REPLACE", "DELETE"):
            raise ValueError("changetype is not valid.")

        payload = {
            "rrsets": [
                {
                    "name": "_acme-challenge" + "." + domain_name + ".",
                    "type": "TXT",
                    "ttl": 60,
                    "changetype": changetype,
                    "records": [{"content": f'"{domain_dns_value}"', "disabled": False}],
                }
            ]
        }
        self.logger.debug(f"PowerDNS domain name: {domain_name}")
        self.logger.debug(f"PowerDNS payload: {payload}")

        apex_domain = self.validate_powerdns_zone(domain_name)
        url = self.powerdns_api_url + "/" + apex_domain
        self.logger.debug(f"apex_domain: {apex_domain}")
        self.logger.debug(f"url: {url}")

        try:
            response = requests.patch(
                url, data=json.dumps(payload), headers={"X-API-Key": self.powerdns_api_key}
            )
            self.logger.debug(f"PowerDNS response: {response.status_code}, {response.text}")
        except Exception as e:
            self.logger.error(f"Unable to communicate with PowerDNS API: {e}")
            raise e

        # Per https://doc.powerdns.com/authoritative/http-api/zone.html:
        # PATCH /servers/{server_id}/zones/{zone_id}
        # Creates/modifies/deletes RRsets present in the payload and their comments.
        # Returns 204 No Content on success.
        if response.status_code != 204:
            raise ValueError(f"Error creating or deleting PowerDNS record: {response.text}")

    def create_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record(domain_name, domain_dns_value, "REPLACE")

    def delete_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record(domain_name, domain_dns_value, "DELETE")
