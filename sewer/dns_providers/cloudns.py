try:
    cloudns_dependencies = True
    from cloudns_api import record
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

    def _split_domain_name(self, domain_name):
        """ClouDNS requires the domain name and host to be split."""
        full_domain_name = '_acme-challenge.{}'.format(domain_name)
        domain_parts = full_domain_name.split(".")

        domain_name = ".".join(domain_parts[-2:])
        host = ".".join(domain_parts[:-2])

        if host == "_acme-challenge.*":
            host = "_acme-challenge"

        return domain_name, host

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name, host = self._split_domain_name(domain_name)
        response = record.create(
            domain_name=domain_name, host=host, record_type="TXT", record=domain_dns_value, ttl=60
        )

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name, host = self._split_domain_name(domain_name)
        response = record.list(domain_name=domain_name, host=host, record_type="TXT")

        for record_id, item in response.payload.items():
            if item["record"] == domain_dns_value:
                response = record.delete(domain_name=domain_name, record_id=record_id)
                break
