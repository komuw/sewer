from cloudns_api import record

from . import common


class ClouDNSDns(common.BaseDns):

    dns_provider_name = "cloudns"

    def _split_domain_name(self, full_domain_name):
        """ClouDNS requires the domain name and host to be split."""
        domain_parts = full_domain_name.split('.')

        if (len(domain_parts) < 3):
            domain_name = full_domain_name
            host = ''
        else:
            domain_name = '.'.join(domain_parts[-2:])
            host = '.'.join(domain_parts[:-2])

        return domain_name, host

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name, host = self._split_domain_name(domain_name)
        response = record.create(domain_name=domain_name, host=host,
                                 record_type='TXT', record=domain_dns_value,
                                 ttl=60)

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name, host = self._split_domain_name(domain_name)
        response = record.list(domain_name=domain_name, host=host,
                               record_type='TXT')

        for record_id, item in response.payload.items():
            if item['record'] == domain_dns_value:
                response = record.delete(domain_name=domain_name,
                                         record_id=record_id)
                break
