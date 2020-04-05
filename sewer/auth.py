import logging
from typing import Sequence, Tuple


class ValidationMethod:
    def __init__(self, label: str, id_type: str, supported: bool):
        self.label = label
        self.id_type = id_type


supported_validations = {
    "http-01": ValidationMethod("http-01", "dns", True),
    "dns-01": ValidationMethod("dns-01", "dns", True),
}


class BaseAuth(object):
    """ Abstract base class for providers of key authorizations that are
    responsible for taking the challenge info they're given and posting it
    where the ACME server can find it, optionally verifying that the
   challenge is properly published, as well as for cleaning up after
    validation is complete.

    NB: BaseDns is a shim for legacy DNS providers, and BaseHttp is deprecated.

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
        chal_types      Sequence[str] set of implemented ACME challenge types

        optional logging control argument(s).  From preferred to legacy:
         *  logger	a configured logging object to use as-is
         *  log_level	level to setup local logger for, defaulting to INFO
         *  LOG_LEVEL   obsolescent legacy version of log_level

        logger will override log_level will override LOG_LEVEL if more than one is passed
        """

        ### FIX ME ### auth_type handling?  and that's not best named, should be challenge_type

        self.chal_types = kwargs.pop("chal_types")
        if not all(ct in supported_validations for ct in self.chal_types):
            raise ValueError("Unsupported challenge type in list: %s" % self.chal_types)

        logger = kwargs.pop("logger", None)
        log_level = kwargs.pop("LOG_LEVEL", "INFO")  # compatibility / obsolescent
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

    def setup_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        for auth in authorizations:
            self.setup_auth(*auth)

    def is_ready_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        return all(self.is_ready_auth(*auth) for auth in authorizations)

    def clear_cert(self, authorizations: Sequence[Tuple[str, str, str]]):
        for auth in authorizations:
            self.clear_auth(*auth)

    def setup_auth(self, domain: str, token: str, key_auth: str):
        "setup one authorization - add dns record, file, etc."
        raise NotImplementedError("setup_auth method must be implemented when setup_cert is not.")

    def is_ready_auth(self, domain: str, token: str, key_auth: str):
        "is one authorization ready for validation?  answer True or False"
        raise NotImplementedError(
            "is_ready_auth method must be implemented when is_ready_cert is not."
        )

    def clear_auth(self, domain: str, token: str, key_auth: str):
        "clear one authorization - remove dns record, file, etc."
        raise NotImplementedError("clear_auth method must be implemented when clear_cert is not.")
