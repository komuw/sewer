from sewer.auth import BaseAuthProvider


class BaseHttp(BaseAuthProvider):
    def __init__(self):
        super(BaseHttp, self).__init__("http-01")

    def create_challenge_file(self, domain_name, token, acme_keyauthorization):
        raise NotImplementedError("delete_auth_record method must be implemented.")

    def fulfill_authorization(self, identifier_auth, token, acme_keyauthorization):
        domain_name = identifier_auth["domain"]
        self.create_challenge_file(domain_name, token, acme_keyauthorization)
        return {
            "domain_name": domain_name,
            "token": token,
            "acme_keyauthorization": acme_keyauthorization,
        }


class CertbotishProvider(BaseHttp):
    def __init__(self, nginx_root="/path/to/www/html/"):
        super(CertbotishProvider, self).__init__("http-01")
        self.nginx_root = nginx_root

    def create_challenge_file(self, domain_name, token, acme_keyauthorization):
        with open(f"{self.nginx_root}/{domain_name}/.well-known/{token}", "w") as fp:
            fp.write(acme_keyauthorization)

    def cleanup_authorization(self, domain_name, token, **kwargs):
        import os

        os.unlink(f"{self.nginx_root}/{domain_name}/.well-known/{token}")
