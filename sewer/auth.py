import logging

from hashlib import sha256
from sewer.lib import safe_base64

### FIX ME ### a few existing providers assume self.log_response exists... need to convert 'em

from sewer.lib import log_response as lib_lr


class BaseAuthProvider(object):
    def __init__(self, logger=None, LOG_LEVEL="INFO"):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(LOG_LEVEL)
            if not self.logger.hasHandlers():
                handler = logging.StreamHandler()
                formatter = logging.Formatter("%(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

        ### hack for compatibility with some (3?) existing dns providers
        self.log_response = lib_lr

    def fulfill_authorization(self, identifier_auth, token, acme_keyauthorization):
        """
        Called by the client to create the required authorization resource. This Could be a dns record (for dns-01)
        or a challange file hosted on the filesystem.

        This method must return a dictionary which are the cleanup_kwargs used in the cleanup_authorization method below
        """
        raise NotImplementedError("fulfill_authorization method must be implemented.")

    def cleanup_authorization(self, **cleanup_kwargs):
        """
        called after the cert is aquired to cleanup any authorization resources created in the fulfill_authorization method above.
        """
        raise NotImplementedError("cleanup_authorization method must be implemented.")


##########

def dns_challenge(key_auth: str) -> str:
    "return safe-base64 of hash of key_auth; used for dns response"

    return safe_base64(sha256(key_auth.encode("utf8")).digest())


class BaseDns(BaseAuthProvider):
    def __init__(self, **kwargs):
        super(BaseDns, self).__init__(kwargs)
        self.auth_type = "dns-01"

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

    def fulfill_authorization(self, identifier_auth, token, acme_keyauthorization):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme-18#section-8.4
        A client fulfills this challenge by constructing a key authorization
        from the "token" value provided in the challenge and the client's
        account key.  The client then computes the SHA-256 digest [FIPS180-4]
        of the key authorization.

        The record provisioned to the DNS contains the base64url encoding of
        this digest.  The client constructs the validation domain name by
        prepending the label "_acme-challenge" to the domain name being
        validated, then provisions a TXT record with the digest value under
        that name.  For example, if the domain name being validated is
        "example.org", then the client would provision the following DNS
        record:
        """
        domain_name = identifier_auth["domain"]
        txt_value = dns_challenge(acme_keyauthorization)
        self.create_dns_record(domain_name, txt_value)
        return {"domain_name": domain_name, "value": txt_value}

    def cleanup_authorization(self, **kwargs):
        self.delete_dns_record(kwargs["domain_name"], kwargs["value"])


##########

class BaseHttp(BaseAuthProvider):
    def __init__(self, **kwargs):
        super(BaseHttp, self).__init__(**kwargs)
        self.auth_type = "http-01"

    def create_challenge_file(self, domain_name, token, acme_keyauthorization):
        """
        Method that creates/add an http challange record file.

        https://tools.ietf.org/html/draft-ietf-acme-acme-18#section-8.3
        A client fulfills this challenge by constructing a key authorization
        from the "token" value provided in the challenge and the client's
        account key.  The client then provisions the key authorization as a
        resource on the HTTP server for the domain in question.

        The path at which the resource is provisioned is comprised of the
        fixed prefix "/.well-known/acme-challenge/", followed by the "token"
        value in the challenge.  The value of the resource MUST be the ASCII
        representation of the key authorization.
        """
        raise NotImplementedError("create_challenge_file method must be implemented.")

    def delete_challenge_file(self, domain_name, token):
        """
        Method that deletes/removes a http challenge record file

        :param domain_name: :string: The domain/subdomain name whose record ought to be
            deleted/removed.
        :param token: :string: The value/content of the record that will be
            deleted/removed for the given domain/subdomain

        This method should return None
        """
        raise NotImplementedError("delete_challenge_file method must be implemented.")

    def fulfill_authorization(self, identifier_auth, token, acme_keyauthorization):
        domain_name = identifier_auth["domain"]
        self.create_challenge_file(domain_name, token, acme_keyauthorization)
        return {
            "domain_name": domain_name,
            "token": token,
            "acme_keyauthorization": acme_keyauthorization,
        }

    def cleanup_authorization(self, **kwargs):
        self.delete_challenge_file(kwargs["domain_name"], kwargs["token"])
