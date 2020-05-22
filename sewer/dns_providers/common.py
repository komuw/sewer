from hashlib import sha256
from typing import Any, Dict, Sequence

from sewer.auth import ErrataItemType, ProviderBase
from sewer.lib import safe_base64


def dns_challenge(key_auth: str) -> str:
    "return safe-base64 of hash of key_auth; used for dns response"

    return safe_base64(sha256(key_auth.encode("utf8")).digest())


class BaseDns(ProviderBase):
    """
    Shim for legacy DNS provider interface.
    """

    def __init__(self, **kwargs: Any) -> None:
        if "chal_types" not in kwargs:
            kwargs["chal_types"] = ["dns-01"]
        super().__init__(**kwargs)

    ### shim methods

    def setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        for chal in challenges:
            self.create_dns_record(chal["ident_value"], dns_challenge(chal["key_auth"]))
        return []

    def unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        return []

    def clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        for chal in challenges:
            self.delete_dns_record(chal["ident_value"], dns_challenge(chal["key_auth"]))
        return []

    ### legacy DNS methods

    def create_dns_record(self, domain_name, domain_dns_value):
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

    def delete_dns_record(self, domain_name, domain_dns_value):
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
