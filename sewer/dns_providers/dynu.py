from sewer import auth
from sewer import lib
import requests


class DynuDns(auth.DNSProviderBase):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def setup(self, challenges):
        for challenge in challenges:
            fqdn = challenge['ident_value']
            txt_value = lib.dns_challenge(challenge['key_auth'])
            self.add_txt_record(fqdn, txt_value)

    def unpropagated(self, challenge):
        return []

    def clear(self, challenges):
        for challenge in challenges:
            fqdn = challenge['ident_value']
            self.remove_txt_record(fqdn)

    def add_txt_record(self, fqdn, txt_value):
        domain_id = self.get_domain_id(fqdn)

        try:
            self.get_txt_record_id(domain_id)
            self.remove_txt_record(fqdn)
        finally:
            r = requests.post('https://api.dynu.com/v2/dns/' + domain_id + '/record',
                              headers={'API-Key': self.api_key},
                              json={"nodeName": "_acme-challenge",
                                    "hostname": "_acme-challenge." + fqdn,
                                    "recordType": "TXT",
                                    "ttl": 30,
                                    "state": True,
                                    "textData": txt_value})

            if r.status_code != 200:
                raise Exception('Unable to add TXT record')

            return

    def remove_txt_record(self, fqdn):
        domain_id = self.get_domain_id(fqdn)

        try :
            record_id = self.get_txt_record_id(domain_id)
        except Exception:
            return

        r = requests.delete('https://api.dynu.com/v2/dns/' + domain_id + '/record/' + record_id,
                            headers={'API-Key': self.api_key})

        if r.status_code != 200:
            raise Exception('Unable to remove TXT record')

    def get_domain_id(self, fqdn):
        r = requests.get('https://api.dynu.com/v2/dns', headers={'API-Key': self.api_key})

        if r.status_code == 200:
            for domain in r.json()['domains']:
                if domain['name'] == fqdn:
                    return str(domain['id'])

        raise Exception('Unable to get domain id')

    def get_txt_record_id(self, domain_id):
        r = requests.get('https://api.dynu.com/v2/dns/' + domain_id + '/record', headers={'API-Key': self.api_key})

        if r.status_code == 200:
            for record in r.json()['dnsRecords']:
                if record['recordType'] == 'TXT':
                    return str(record['id'])

        raise Exception('Unable to get TXT record id')
