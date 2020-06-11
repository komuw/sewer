try:
    cloudns_dependencies = True
    import cloudns_api
except ImportError:
    cloudns_dependencies = False

from . import common

class ClouDNSDns(common.BaseDns):

    dns_provider_name = "cloudns"

    def __init__(self, *args, **kwargs):

        if not cloudns_dependencies:
            raise ImportError(
                """You need to install ClouDNSDns dependencies. run; pip3 install sewer[cloudns]"""
            )

        super(ClouDNSDns, self).__init__(*args, **kwargs)
        self.records = {}

    def _find_dns_zone(self, domain):
        zones = cloudns_api.zone.list().payload
        match = {'name': ''}
        for zone in zones:
            if zone['zone'] != 'domain':
                continue
            pos = domain.find(zone['name'])
            self.logger.debug("Trying to match zone: %s", repr(zone))
            if pos != -1:
                # this is the zone
                self.logger.debug("Got a match: {}".format(repr(zone)))
                if match['name']:
                    if match['priority'] > pos:
                        match = {'name': zone['name'], 'priority': pos}
                else:
                    match = {'name': zone['name'], 'priority': pos}
        if not match['name']:
            return False
        zonename = match['name']
        self.logger.debug("Matched domain name: %s", zonename)
        return zonename

    def create_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("create_dns_record")
        zone, host = self._find_dns_zone(domain_name), "_acme-challenge"
        if not zone:
            self.logger.info("No matching zone found in ClouDNS for domain name " + domain_name)
            raise Exception("No matching zone found in ClouDNS for domain name " + domain_name)

        response = cloudns_api.record.create(
            domain_name=zone, host=host, record_type="TXT", record=domain_dns_value, ttl=60
        )

        if not response.success:
            self.logger.info("ClouDNS could not create DNS record.")
            raise Exception("ClouDNS responded with an error.")

        self.records[domain_name] = {'id': response.payload['data']['id'], 'zone': zone}
        self.logger.info("create_dns_record_success")
        return

    def delete_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("delete_dns_record")
        response = cloudns_api.record.delete(self.records[domain_name]['zone'], self.records[domain_name]['id'])

        if not response.success:
            self.logger.info("ClouDNS could not find DNS record to delete.")
            raise Exception("ClouDNS responded with an error.")
