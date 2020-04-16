import logging
from .lib import create_logger


class BaseAuthProvider(object):
    def __init__(self, auth_type, LOG_LEVEL="INFO"):
        self.LOG_LEVEL = LOG_LEVEL
        self.dns_provider_name = self.__class__.__name__

        self.logger = create_logger(__name__, self.LOG_LEVEL)

        self.auth_type = auth_type

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
