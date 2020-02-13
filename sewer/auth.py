import logging


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

    def create_auth_record(self, name, value):
        raise NotImplementedError("create_auth_record method must be implemented.")

    def delete_auth_record(self, name, value):
        raise NotImplementedError("delete_auth_record method must be implemented.")

    def fulfill_authorization(self, identifier_auth, value, acme_keyauthorization):
        """
        TODO: docs here
        """
        name = identifier_auth["domain"]
        self.create_auth_record(name, value)

        responder = {
            "challenge_url": identifier_auth["challenge_url"],
            "acme_keyauthorization": acme_keyauthorization,
            "authorization_url": identifier_auth["url"],
        }
        cleanup = {"name": name, "value": value}
        return (responder, cleanup)

    def cleanup(self, record):
        self.delete_auth_record(record["name"], record["value"])
