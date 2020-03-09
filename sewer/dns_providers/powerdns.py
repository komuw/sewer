import json
import requests

from . import common


class PowerDNSDns(common.BaseDns):
    dns_provider_name = "powerdns"

    def __init__(self, powerdns_api_key, powerdns_api_url):
        self.powerdns_api_key = powerdns_api_key
        self.powerdns_api_url = powerdns_api_url
        super(PowerDNSDns, self).__init__()


    def _common_dns_record(self, domain_name, domain_dns_value, changetype):
        if changetype not in ('REPLACE', 'DELETE'):
            raise ValueError("changetype is not valid.")

        payload = {
            "rrsets": [
                {
                    'name': '_acme-challenge' + '.' + domain_name + '.',
                    "type": "TXT",
                    "ttl": 60,
                    "changetype": changetype,
                    "records": [
                        {
                            "content": f'"{domain_dns_value}"',
                            "disabled": False
                        }
                    ]
                }
            ]
        }

        powerdns_response = requests.patch(
            self.powerdns_api_url + '/' + domain_name,
            data=json.dumps(payload),
            headers={'X-API-Key': self.powerdns_api_key}
        )


    def create_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record(domain_name, domain_dns_value, "REPLACE")



    def delete_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record(domain_name, domain_dns_value, "DELETE")
