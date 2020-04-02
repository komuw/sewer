from sewer.auth import BaseAuthProvider


class BaseHttp(BaseAuthProvider):
    def __init__(self):
        super(BaseHttp, self).__init__("http-01")

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
