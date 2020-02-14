# the test dir is a sub dir of sewer/sewer so as
# not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import mock
import cryptography
from unittest import TestCase

import sewer
from sewer.config import ACME_DIRECTORY_URL_STAGING

from . import test_utils


class TestClient(TestCase):
    """
    Todo:
        - mock time.sleep
        - make this tests DRY
        - add tests for the cli
        - modularize this tests
        - separate happy path tests from sad path tests.
            eg test_get_identifier_authorization_is_called and test_get_identifier_authorization_is_not_called
            should be in different testClasses
    """

    def setUp(self):
        self.domain_name = "example.com"
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.auth_provider = test_utils.ExmpleAuthProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name,
                auth_provider=self.auth_provider,
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
            )

    def tearDown(self):
        pass

    def test_get_get_acme_endpoints_failure_results_in_exception(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse(status_code=409)
            mock_requests_get.return_value = test_utils.MockResponse(status_code=409)

            def mock_create_acme_client():
                sewer.Client(
                    domain_name="example.com",
                    auth_provider=test_utils.ExmpleAuthProvider(),
                    ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                )

            self.assertRaises(ValueError, mock_create_acme_client)
            with self.assertRaises(ValueError) as raised_exception:
                mock_create_acme_client()
            self.assertIn("Error while getting Acme endpoints", str(raised_exception.exception))

    def test_user_agent_is_generated(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            for i in ["python-requests", "sewer", "https://github.com/komuw/sewer"]:
                self.assertIn(i, self.client.User_Agent)

    def test_certificate_key_is_generated(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            certificate_key = self.client.certificate_key

            certificate_key_private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
                certificate_key.encode(),
                password=None,
                backend=cryptography.hazmat.backends.default_backend(),
            )
            self.assertIsInstance(
                certificate_key_private_key, cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey
            )

    def test_account_key_is_generated(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            account_key = self.client.account_key

            account_key_private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
                account_key.encode(),
                password=None,
                backend=cryptography.hazmat.backends.default_backend(),
            )
            self.assertIsInstance(
                account_key_private_key, cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey
            )

    def test_acme_registration_is_done(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("sewer.Client.acme_register") as mock_acme_registration:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.client.cert()
            self.assertTrue(mock_acme_registration.called)

    def test_acme_registration_failure_doesnt_result_in_certificate(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse(status_code=400)
            mock_requests_get.return_value = test_utils.MockResponse(status_code=400)

            def mock_get_certificate():
                self.client.cert()

            self.assertRaises(ValueError, mock_get_certificate)
            with self.assertRaises(ValueError) as raised_exception:
                mock_get_certificate()
            self.assertIn("Error while registering", str(raised_exception.exception))

    def test_get_identifier_authorization_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.Client.get_identifier_authorization"
        ) as mock_get_identifier_authorization:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            mock_get_identifier_authorization.return_value = {
                "domain": "example.com",
                "url": "http://localhost",
                "wildcard": None,
                "token": "token",
                "challenge_url": "challenge_url",
            }
            self.client.cert()
            self.assertTrue(mock_get_identifier_authorization.called)

    def test_get_identifier_authorization_is_not_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("sewer.Client.acme_register") as mock_acme_register:
            mock_requests_post.return_value = test_utils.MockResponse(status_code=400)
            mock_requests_get.return_value = test_utils.MockResponse(status_code=400)
            mock_acme_register.return_value = test_utils.MockResponse(status_code=201)

            def mock_get_certificate():
                self.client.cert()

            self.assertRaises(ValueError, mock_get_certificate)
            with self.assertRaises(ValueError) as raised_exception:
                mock_get_certificate()
            self.assertIn(
                "Error applying for certificate issuance", str(raised_exception.exception)
            )

    def test_respond_to_challenge_called(self):
        pending_status_mock = mock.Mock()
        pending_status_mock.json.return_value = {"status": "pending"}

        valid_status_mock = mock.Mock()
        valid_status_mock.json.return_value = {"status": "valid"}

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.Client.respond_to_challenge"
        ) as mock_respond_to_challenge, mock.patch(
            "sewer.Client.check_authorization_status"
        ) as mock_check_authorization_status:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            mock_check_authorization_status.side_effect = [
                # 1st call returns 'pending', so respond_to_challenge has to be made
                pending_status_mock,
                # 2nd call returns 'valid', so loop breaks
                valid_status_mock,
            ]
            self.client.cert()
            self.assertTrue(mock_respond_to_challenge.called)

    def test_check_authorization_status_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.Client.check_authorization_status"
        ) as mock_check_authorization_status:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.client.cert()
            self.assertTrue(mock_check_authorization_status.called)

    def test_get_certificate_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("sewer.Client.get_certificate") as mock_get_certificate:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.client.cert()
            self.assertTrue(mock_get_certificate.called)

    def test_certificate_is_issued(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            for i in ["-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----"]:
                self.assertIn(i, self.client.cert())

    def test_certificate_is_not_issued(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.Client.get_identifier_authorization"
        ) as mock_get_identifier_authorization, mock.patch(
            "sewer.Client.acme_register"
        ) as mock_acme_register:
            mock_requests_post.return_value = test_utils.MockResponse(status_code=400)
            mock_requests_get.return_value = test_utils.MockResponse(status_code=400)
            mock_get_identifier_authorization.return_value = {
                "domain": "example.com",
                "url": "http://localhost",
                "wildcard": None,
                "token": "token",
                "challenge_url": "challenge_url",
            }
            mock_acme_register.return_value = test_utils.MockResponse(status_code=409)

            def mock_get_certificate():
                self.client.cert()

            self.assertRaises(ValueError, mock_get_certificate)

            with self.assertRaises(ValueError) as raised_exception:
                mock_get_certificate()
            self.assertIn("Error applying for certificate", str(raised_exception.exception))

    def test_certificate_is_issued_for_renewal(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            for i in ["-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----"]:
                self.assertIn(i, self.client.renew())

    def test_right_args_to_client(self):
        def mock_instantiate_client():
            self.client = sewer.Client(
                domain_name=self.domain_name,
                auth_provider=self.auth_provider,
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                domain_alt_names="domain_alt_names",
            )

        with self.assertRaises(ValueError) as raised_exception:
            mock_instantiate_client()
        self.assertIn(
            "domain_alt_names should be of type:: None or list", str(raised_exception.exception)
        )


class TestClientForSAN(TestClient):
    """
    Test Acme client for SAN certificates.
    """

    def setUp(self):
        self.domain_name = "exampleSAN.com"
        self.domain_alt_names = [
            "blog.exampleSAN.com",
            "staging.exampleSAN.com",
            "www.exampleSAN.com",
        ]
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,
                domain_alt_names=self.domain_alt_names,
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
            )
        super(TestClientForSAN, self).setUp()


class TestClientForWildcard(TestClient):
    """
    Test Acme client for wildard certificates.
    """

    def setUp(self):
        self.domain_name = "*.exampleSTARcom"
        self.domain_alt_names = [
            "blog.exampleSAN.com",
            "staging.exampleSAN.com",
            "www.exampleSAN.com",
        ]
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,
                domain_alt_names=self.domain_alt_names,
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_AUTH_STATUS_MAX_CHECKS=1,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
            )
        super(TestClientForWildcard, self).setUp()


class TestClientDnsApiCompatibility(TestCase):
    """
    Test Acme client for the existing dns provider api.
    """

    def setUp(self):
        self.domain_name = "example.com"
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
            )

    def test_get_get_acme_endpoints_failure_results_in_exception_with(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse(status_code=409)
            mock_requests_get.return_value = test_utils.MockResponse(status_code=409)

            def mock_create_acme_client():
                sewer.Client(
                    domain_name="example.com",
                    dns_class=test_utils.ExmpleDnsProvider(),  # NOTE: dns_class used here
                    ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                )

            self.assertRaises(ValueError, mock_create_acme_client)
            with self.assertRaises(ValueError) as raised_exception:
                mock_create_acme_client()
            self.assertIn("Error while getting Acme endpoints", str(raised_exception.exception))

    def test_create_dns_record_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.tests.test_utils.ExmpleDnsProvider.create_dns_record"
        ) as mock_create_dns_record:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.client.cert()
            self.assertTrue(mock_create_dns_record.called)

    def test_delete_dns_record_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.tests.test_utils.ExmpleDnsProvider.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.client.cert()
            self.assertTrue(mock_delete_dns_record.called)

    def test_right_args_to_client(self):
        def mock_instantiate_client():
            self.client = sewer.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,  # NOTE: dns_class used here
                ACME_REQUEST_TIMEOUT=1,
                ACME_AUTH_STATUS_WAIT_PERIOD=0,
                ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                domain_alt_names="domain_alt_names",
            )


# TEST cli
# from unittest import TestCase
# from funniest.command_line import main

# class TestConsole(TestCase):
#     def test_basic(self):
#         main()
