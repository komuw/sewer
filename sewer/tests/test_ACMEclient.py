# the test dir is a sub dir of sewer/sewer so as
# not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import mock
import cryptography
from unittest import TestCase

import sewer

from . import test_utils


class TestACMEclient(TestCase):
    """
    Todo:
        - mock time.sleep
        - make this tests DRY
        - add tests for the cli
        - modularize this tests
    """

    def setUp(self):
        self.domain_name = 'example.com'
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,
                ACME_CHALLENGE_WAIT_PERIOD=0)

    def tearDown(self):
        pass

    def test_user_agent_is_generated(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)

            for i in [
                    'python-requests', 'sewer', 'https://github.com/komuW/sewer'
            ]:
                self.assertIn(i, self.client.User_Agent)

    def test_certificate_key_is_generated(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            certificate_key = self.client.certificate_key

            certificate_key_private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
                certificate_key,
                password=None,
                backend=cryptography.hazmat.backends.default_backend())
            self.assertIsInstance(
                certificate_key_private_key,
                cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey)

    def test_account_key_is_generated(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            account_key = self.client.account_key

            account_key_private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
                account_key,
                password=None,
                backend=cryptography.hazmat.backends.default_backend())
            self.assertIsInstance(
                account_key_private_key,
                cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey)

    def test_certificate_chain_is_generated(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.assertIsInstance(self.client.certificate_chain, basestring)

    def test_acme_registration_is_done(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.Client.acme_register') as mock_acme_registration:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_acme_registration.called)

    def test_get_challenge_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.Client.get_challenge') as mock_get_challenge:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            mock_get_challenge.return_value = 'dns_token', 'dns_challenge_url'
            self.client.cert()
            self.assertTrue(mock_get_challenge.called)

    def test_create_dns_record_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.tests.test_utils.ExmpleDnsProvider.create_dns_record'
                ) as mock_create_dns_record:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_create_dns_record.called)

    def test_notify_acme_challenge_set_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.Client.notify_acme_challenge_set'
                ) as mock_notify_acme_challenge_set:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_notify_acme_challenge_set.called)

    def test_check_challenge_status_set_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.Client.check_challenge_status'
                ) as mock_check_challenge_status:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_check_challenge_status.called)

    def test_delete_dns_record_not_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.tests.test_utils.ExmpleDnsProvider.delete_dns_record'
                ) as mock_delete_dns_record:
            content = """
                          {"status": "pending", "challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertFalse(mock_delete_dns_record.called)

    def test_delete_dns_record_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.tests.test_utils.ExmpleDnsProvider.delete_dns_record'
                ) as mock_delete_dns_record:
            content = """
                          {"status": "valid", "challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_delete_dns_record.called)

    def test_get_certificate_is_called(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'sewer.Client.get_certificate') as mock_get_certificate:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            self.client.cert()
            self.assertTrue(mock_get_certificate.called)

    def test_certificate_is_issued(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            content = """
                          {"challenges": [{"type": "dns-01", "token": "example-token", "uri": "example-uri"}]}
                      """
            mock_requests_post.return_value = test_utils.MockResponse(
                content=content)
            mock_requests_get.return_value = test_utils.MockResponse(
                content=content)
            for i in [
                    '-----BEGIN CERTIFICATE-----', '-----END CERTIFICATE-----'
            ]:
                self.assertIn(i, self.client.cert())


# TEST cli
# from unittest import TestCase
# from funniest.command_line import main

# class TestConsole(TestCase):
#     def test_basic(self):
#         main()
