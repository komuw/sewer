import logging
import base64


def calculate_safe_base64(un_encoded_data):
    """
    takes in a string or bytes
    returns a string
    """
    if isinstance(un_encoded_data, str):
        un_encoded_data = un_encoded_data.encode("utf8")
    r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
    return r.decode("utf8")


class BaseAuthProvider(object):
    def __init__(self, auth_type, LOG_LEVEL="INFO"):
        self.LOG_LEVEL = LOG_LEVEL
        self.dns_provider_name = self.__class__.__name__

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.LOG_LEVEL)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.auth_type = auth_type

    def log_response(self, response):
        """
        renders a python-requests response as json or as a string
        """
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    def get_identifier_auth(self, authorization_response, url):
        """
        grab the identifier authorization info for the implimented auth challenge type
        """
        domain = authorization_response["identifier"]["value"]
        wildcard = authorization_response.get("wildcard")
        if wildcard:
            domain = "*." + domain

        for i in authorization_response["challenges"]:
            if i["type"] == self.auth_type:
                challenge = i
                challenge_token = challenge["token"]
                challenge_url = challenge["url"]

                return {
                    "domain": domain,
                    "url": url,
                    "wildcard": wildcard,
                    "token": challenge_token,
                    "challenge_url": challenge_url,
                }

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
