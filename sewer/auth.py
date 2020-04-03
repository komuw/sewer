import logging
from typing import Sequence, Tuple

from hashlib import sha256
from sewer.lib import safe_base64

### FIX ME ### a few existing providers assume self.log_response exists... need to convert 'em

from sewer.lib import log_response as lib_lr


class BaseAuth(object):
    """
    Abstract base class for providers of key authorizations that are responsible
    for taking the challenge info they're given and posting it where the ACME server
    can find it, as well as for cleaning up after validation is complete.

    There are layers of interface for the challenge setup & clear operations.  The
    newest, and the one that will be called directly from sewer's ACME code, passes
    a list of (domain, token, key_auth) containing all of the authorizations that
    must be validated before a certificate can issue.  These are the *_cert methods.

    The layer below *_cert are interfaces to setup and clean a single authorization
    per call, and are names *_auth.  They take three arguments, same as each item
    in the list passed to *_cert.  Aside from naming, these are pretty much the
    same as the original dns-only provider interface.

    The third level is a temporary one for compatibility with unconverted dns
    providers that were written before this was introduced.  create_dns_record and
    delete_dns_record are obsolescent, and will be removed when there are no
    provders left in the tree that use them.

    The implementation of the *_cert methods here just loops, calling *_auth for
    each item in the authprizations list.  So providers that have to deal with one
    auth at a time can just implement that.  Some providers may be able to work
    more efficently if they can see all the items at once, and those will prefer
    to implement *_cert, overriding the versions here.

    __init__ arguments protocol:  Taking the lesson from some Django classes that
    were layered like this (and with many leaf users, some outside of the framework),
    it is always declared with only self and **kwargs.  Each layer MUST pop the args
    it knows and wishes to handle, then pass what's left to its immediate base class.
    The end goal is to allow initializing a provider with whatever it needs to
    authenticate to and interact with the DNS system that publishes the challenges.
    Then that can be done outside of sewer's ACME engine (Client class) and passed
    to it ready to use.
    """

    def __init__(self, **kwargs):
        """
        __init__ accepts logging control argument(s).  From preferred to legacy:
         *  logger	a configured logging object to use as-is
         *  log_level	level to setup local logger for, defaulting to INFO
         *  LOG_LEVEL   obsolescent legacy version of log_level

        logger will override log_level will override LOG_LEVEL if more than one is passed
        """

        logger = kwargs.pop("logger", None)
        log_level = kwargs.pop("LOG_LEVEL", "INFO")	# compatibility / obsolescent
        log_level = kwargs.pop("log_level", log_level)
        if kwargs:
            raise ValueError("BaseAuth was passed unrecognized argument(s): %s" % kwargs)

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(log_level)
            if not self.logger.hasHandlers():
                handler = logging.StreamHandler()
                formatter = logging.Formatter("%(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

        ### hack for compatibility with some (3?) existing dns providers
        self.log_response = lib_lr

    def setup_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        for auth in authorizations:
            self.setup_auth(*auth)

    def is_ready_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        for auth in authorizations:
            self.is_ready_auth(*auth)

    def clear_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        for auth in authorizations:
            self.clear_auth(*auth)

    def setup_auth(self, domain: str, token: str, key_auth: str):
        "setup one authorization - add dns record, file, etc."
        raise NotImplementedError("setup_auth method must be implemented when setup_cert is not.")

    def is_ready_auth(self, domain: str, token: str, key_auth: str):
        "is one authorization ready for validation?  answer True or False"
        raise NotImplementedError("is_ready_auth method must be implemented when is_ready_cert is not.")


    def clear_auth(self, domain: str, token: str, key_auth: str):
        "clear one authorization - remove dns record, file, etc."
        raise NotImplementedError("clear_auth method must be implemented when clear_cert is not.")


def dns_challenge(key_auth: str) -> str:
    "return safe-base64 of hash of key_auth; used for dns response"

    return safe_base64(sha256(key_auth.encode("utf8")).digest())


class BaseDns(BaseAuth):
    """
    BaseDns provides a compatibility layer in the *_auth methods.  These convert
    the "standard" three arguments into the two that are needed by legacy dns
    providers, allowing them to work behind these new interfaces.  That's not to
    say that they have to do that, and if a provider can update multiple texts at
    a time, it can take advantage of the *_cert interfaces.  Whatever works best...
    """

    def __init__(self, **kwargs):
        super(BaseDns, self).__init__(**kwargs)
        self.auth_type = "dns-01"

    def setup_auth(self, domain: str, token: str, key_auth: str):
        "shim to use legacy create_dns_record method"

        self.create_dns_record(domain, dns_challenge(key_auth))

    def clear_auth(self, domain: str, token: str, key_auth: str):
        "shim to use legacy delete_dns_record method"

        self.delete_dns_record(domain, dns_challenge(key_auth))

    ### FIX ME ### left the legacy DNS provider methods here for compatibility and documentation

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


class BaseHttp(BaseAuth):
    """
    Since support for http providers is new at about the same time as the new
    interface, there's no need for backwards compatible shims in BaseHttp.
    """

    def __init__(self, **kwargs):
        super(BaseHttp, self).__init__(**kwargs)
        self.auth_type = "http-01"
