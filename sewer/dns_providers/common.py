from structlog import get_logger


class BaseDns(object):
    """
    """

    def __init__(self):
        self.dns_provider_name = None
        if self.dns_provider_name is None:
            raise ValueError(
                'The class attribute dns_provider_name ought to be defined.')

        self.logger = get_logger(__name__).bind(
            dns_provider_name=self.dns_provider_name)

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('create_dns_record')
        raise NotImplementedError(
            'create_dns_record method must be implemented.')

    def delete_dns_record(self, domain_name, dns_record_id):
        self.logger.info('delete_dns_record')
        raise NotImplementedError(
            'delete_dns_record method must be implemented.')
