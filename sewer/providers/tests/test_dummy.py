from unittest import mock
from unittest import TestCase

from sewer.providers import http_dummy


authorizations = (
    ("example.com", "token123", "key secret 123"),
    ("www.example.com", "token456", "key secret 456"),
    ("www2.example.com", "token789", "key secret 789"),
)


class TestDummy(TestCase):

    def setup(self):
        pass

    def tearDown(self):
        pass

    def test_dummy_http_cert_from_cert(self):
        provider = http_dummy.HttpDummyCert()
        provider.setup_cert(authorizations)
        self.assertTrue(provider.is_ready_cert(authorizations))
        provider.clear_cert(authorizations)
        self.assertFalse(provider.active_challenges)

    def test_dummy_http_auth_from_cert(self):
        provider = http_dummy.HttpDummyAuth()
        provider.setup_cert(authorizations)
        self.assertTrue(provider.is_ready_cert(authorizations))
        provider.clear_cert(authorizations)
        self.assertFalse(provider.active_challenges)

    def test_dummy_http_auth_from_auth(self):
        provider = http_dummy.HttpDummyAuth()
        for auth in authorizations:
            provider.setup_auth(*auth)
            self.assertTrue(provider.is_ready_auth(*auth))
            provider.clear_auth(*auth)
            self.assertFalse(provider.active_challenges)
