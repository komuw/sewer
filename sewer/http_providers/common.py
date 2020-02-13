from sewer.auth import BaseAuthProvider


class BaseHttp(BaseAuthProvider):
    def __init__(self):
        super(BaseHttp, self).__init__("http-01")


class CertbotishProvider(BaseHttp):
    def create_auth_record(self, name, value):
        with open("/path/to/www/html/.well-known/{name}", "w") as fp:
            fp.write(value)

    def delete_auth_record(self, name, value):
        import os

        os.unlink("/path/to/www/html/.well-known/{name}")
