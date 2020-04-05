from sewer.auth import BaseAuth

from hashlib import sha256
from sewer.lib import safe_base64

from sewer.lib import log_response as lib_lr


def dns_challenge(key_auth: str) -> str:
    "return safe-base64 of hash of key_auth; used for dns response"

    return safe_base64(sha256(key_auth.encode("utf8")).digest())


class BaseDns(BaseAuth):
    """
    BaseDns provides a legacy compatibility layer in the *_auth methods.
    These convert the "standard" three arguments into the two that are
    needed by legacy dns providers, allowing them to work behind these new
    interfaces.

    Ideally, all the legacy DNS providers will eventually be updated and
    this interface shim can be decomissioned.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("chal_types", ["dns-01"])
        super(BaseDns, self).__init__(**kwargs)

        ### hack for compatibility with some (3?) existing dns providers
        self.log_response = lib_lr

    def setup_auth(self, domain: str, token: str, key_auth: str) -> None:
        "shim to use legacy create_dns_record method"

        self.create_dns_record(domain, dns_challenge(key_auth))

    def is_ready_auth(self, domain: str, token: str, key_auth: str) -> bool:
        "nothing in legacy to shim for, so just report ready"
        return True

    def clear_auth(self, domain: str, token: str, key_auth: str) -> None:
        "shim to use legacy delete_dns_record method"

        self.delete_dns_record(domain, dns_challenge(key_auth))

    ### FIX ME ### left the legacy DNS provider methods here for compatibility and documentation

    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        """
        Method that creates/adds a dns TXT record for a domain/subdomain name on
        a chosen DNS provider.

        :param domain_name: :string: The domain/subdomain name whose dns record ought to be
            created/added on a chosen DNS provider.
        :param domain_dns_value: :string: The value/content of the TXT record that will be
            created/added for the given domain/subdomain

        This method should return None

        Basic Usage:
            If the value of the `domain_name` variable is example.com and the value of
            `domain_dns_value` is HAJA_4MkowIFByHhFaP8u035skaM91lTKplKld
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
        raise NotImplementedError("create_dns_record method must be implemented.")

    def delete_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        """
        Method that deletes/removes a dns TXT record for a domain/subdomain name on
        a chosen DNS provider.

        :param domain_name: :string: The domain/subdomain name whose dns record ought to be
            deleted/removed on a chosen DNS provider.
        :param domain_dns_value: :string: The value/content of the TXT record that will be
            deleted/removed for the given domain/subdomain

        This method should return None
        """
        raise NotImplementedError("delete_dns_record method must be implemented.")
