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

    def log_response(self, response):
        """
        renders a python-requests response as json or as a string
        """
        try:
            response.content.decode('ascii')  # try and trigger a unicode error.
            log_body = response.json()
        except UnicodeError:
            # unicodeError is a subclass of ValueError so we need to capture it first
            log_body = 'Unicode response.'
        except ValueError:
            log_body = response.content
        return log_body

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        """
        Method that creates/adds a dns TXT record for a domain/subdomain name on
        a chosen DNS provider.

        :param domain_name: :string: The domain/subdomain name whose dns record ought to be
            created/added on a chosen DNS provider.
        :param base64_of_acme_keyauthorization: :string: The value/content of the TXT record that will be
            created/added for the given domain/subdomain

        This method should return None

        Basic Usage:
            If the value of the `domain_name` variable is example.com and the value of
            `base64_of_acme_keyauthorization` is HAJA_4MkowIFByHhFaP8u035skaM91lTKplKld
            Then, your implementation of this method ought to create a DNS TXT record
            whose name is '_acme-challenge' + '.' + domain_name + '.' (ie: _acme-challenge.example.com. )
            and whose value/content is HAJA_4MkowIFByHhFaP8u035skaM91lTKplKld

            Using a dns client like dig(https://linux.die.net/man/1/dig) to do a dns lookup should result
            in something like:
                dig TXT _acme-challenge.example.com
                ...
                ;; ANSWER SECTION:
                _acme-challenge.example.com. 120 IN TXT "HAJA_4MkowIFByHhFaP8u035skaM91lTKplKld"
                _acme-challenge.singularity.brandur.org. 120 IN TXT "9C0DqKC_4MkowIFByHhFaP8u0Zv4z7Wz2IHM91lTKec"
            Optionally, you may also use an online dns client like: https://toolbox.googleapps.com/apps/dig/#TXT/

            Please consult your dns provider on how/format of their DNS TXT records.
            You may also want to consult the cloudflare DNS implementation that is found in this repository.
        """
        self.logger.info('create_dns_record')
        raise NotImplementedError(
            'create_dns_record method must be implemented.')

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        """
        Method that deletes/removes a dns TXT record for a domain/subdomain name on
        a chosen DNS provider.

        :param domain_name: :string: The domain/subdomain name whose dns record ought to be
            deleted/removed on a chosen DNS provider.
        :param base64_of_acme_keyauthorization: :string: The value/content of the TXT record that will be
            deleted/removed for the given domain/subdomain

        This method should return None
        """
        self.logger.info('delete_dns_record')
        raise NotImplementedError(
            'delete_dns_record method must be implemented.')
