# the test dir is a sub dir of sewer/sewer so as
# not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

# Have had to sprinkle the pylint pragma "disable=E1125" in the TestCase
# classes because pylint just won't shut up about missing required keywords
# that are passed as **kwargs.  If I had time to piss away on it the pragma
# could be added to individual calls.  Not!

# Also, you can't write out the pragma in a comment like the above without
# having pylint notice it - and in this case give an error for it at module
# scope.  So reminiscent of the bad side of ol' lint.


from unittest import expectedFailure, mock, TestCase

import cryptography

import sewer.client

from ..config import ACME_DIRECTORY_URL_STAGING
from ..crypto import AcmeKey, AcmeAccount
from ..lib import AcmeRegistrationError
from . import test_utils

LOG_LEVEL = "CRITICAL"

### FIX ME ### even with making the keys new each time, some tests manage to re-register!
# luckily it's working anyway, but it's a good thing most of this will have to be scrapped soon


def keys_for_ACME(no_kid=False):
    acct = AcmeAccount.create("secp256r1")
    ck = AcmeKey.create("secp256r1")
    if not no_kid:
        acct.kid = "https://imagine.acct.kid/here"
    return {"account": acct, "cert_key": ck}


def usual_ACME(no_kid=False):
    res = {
        "ACME_REQUEST_TIMEOUT": 1,
        "ACME_AUTH_STATUS_WAIT_PERIOD": 0,
        "ACME_DIRECTORY_URL": ACME_DIRECTORY_URL_STAGING,
        "LOG_LEVEL": LOG_LEVEL,
    }
    res.update(keys_for_ACME(no_kid))
    return res


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

    # pylint: disable=E1125

    def setUp(self):
        self.domain_name = "example.com"
        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ):

            self.provider = test_utils.ExmpleHttpProvider()
            self.client = sewer.client.Client(
                domain_name=self.domain_name, provider=self.provider, **usual_ACME()
            )

    def tearDown(self):
        pass

    def test_get_get_acme_endpoints_failure_results_in_exception(self):
        with mock.patch(
            "requests.post", return_value=test_utils.MockResponse(status_code=409)
        ), mock.patch("requests.get", return_value=test_utils.MockResponse(status_code=409)):

            def mock_create_acme_client():
                sewer.client.Client(
                    domain_name="example.com",
                    provider=test_utils.ExmpleHttpProvider(),
                    ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                    LOG_LEVEL=LOG_LEVEL,
                    **keys_for_ACME(),
                )

            self.assertRaises(ValueError, mock_create_acme_client)
            with self.assertRaises(ValueError) as raised_exception:
                mock_create_acme_client()
            self.assertIn("Error while getting Acme endpoints", str(raised_exception.exception))

    def test_user_agent_is_generated(self):
        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ):

            for i in ["python-requests", "sewer", "https://github.com/komuw/sewer"]:
                self.assertIn(i, self.client.User_Agent)

    def test_acme_registration_is_done(self):
        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ), mock.patch("sewer.client.Client.acme_register") as mock_acme_registration:

            self.client.cert()
            self.assertTrue(mock_acme_registration.called)

    def test_acme_registration_failure_doesnt_result_in_certificate(self):
        client = sewer.client.Client(
            domain_name=self.domain_name, provider=self.provider, **usual_ACME(no_kid=True)
        )
        with mock.patch(
            "requests.post", return_value=test_utils.MockResponse(status_code=400)
        ), mock.patch("requests.get", return_value=test_utils.MockResponse(status_code=400)):

            with self.assertRaises(AcmeRegistrationError):
                client.get_certificate()

    def test_get_identifier_authorization_is_called(self):
        gia_return_value = {
            "domain": "example.com",
            "url": "http://localhost",
            "wildcard": None,
            "token": "token",
            "challenge_url": "challenge_url",
        }
        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ), mock.patch(
            "sewer.client.Client.get_identifier_authorization", return_value=gia_return_value
        ) as mock_gia:

            self.client.cert()
            self.assertTrue(mock_gia.called)

    def test_get_identifier_authorization_is_not_called(self):
        with mock.patch(
            "requests.post", return_value=test_utils.MockResponse(status_code=400)
        ), mock.patch(
            "requests.get", return_value=test_utils.MockResponse(status_code=400)
        ), mock.patch(
            "sewer.client.Client.acme_register",
            return_value=test_utils.MockResponse(status_code=201),
        ):

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

        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ), mock.patch(
            "sewer.client.Client.respond_to_challenge"
        ) as mock_respond_to_challenge, mock.patch(
            "sewer.client.Client.check_authorization_status"
        ) as mock_check_authorization_status:
            mock_check_authorization_status.side_effect = [
                # 1st call returns 'pending', so respond_to_challenge has to be made
                pending_status_mock,
                # 2nd call returns 'valid', so loop breaks
                valid_status_mock,
            ]

            self.client.cert()
            self.assertTrue(mock_respond_to_challenge.called)

    def test_check_authorization_status_is_called(self):
        with mock.patch("requests.post", return_value=test_utils.MockResponse()), mock.patch(
            "requests.get", return_value=test_utils.MockResponse()
        ), mock.patch("sewer.client.Client.check_authorization_status") as mock_cas:

            self.client.cert()
            self.assertTrue(mock_cas.called)

    def test_get_certificate_is_called(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.client.Client.get_certificate"
        ) as mock_get_certificate:
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
        gia_return_value = {
            "domain": "example.com",
            "url": "http://localhost",
            "wildcard": None,
            "token": "token",
            "challenge_url": "challenge_url",
        }
        with mock.patch(
            "requests.post", return_value=test_utils.MockResponse(status_code=400)
        ), mock.patch(
            "requests.get", return_value=test_utils.MockResponse(status_code=400)
        ), mock.patch(
            "sewer.client.Client.get_identifier_authorization", return_value=gia_return_value
        ), mock.patch(
            "sewer.client.Client.acme_register",
            return_value=test_utils.MockResponse(status_code=409),
        ):

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
            self.client = sewer.client.Client(
                domain_name=self.domain_name,
                provider=self.provider,
                domain_alt_names="domain_alt_names",
                **usual_ACME(),
            )

        with self.assertRaises(ValueError) as raised_exception:
            mock_instantiate_client()
        self.assertIn("None or a list of strings", str(raised_exception.exception))


class TestClientForSAN(TestClient):
    """
    Test Acme client for SAN certificates.
    """

    # pylint: disable=E1125

    def setUp(self):
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
            self.client = sewer.client.Client(
                domain_name="exampleSAN.com",
                dns_class=self.dns_class,
                domain_alt_names=self.domain_alt_names,
                **usual_ACME(),
            )
        super(TestClientForSAN, self).setUp()


class TestClientForWildcard(TestClient):
    """
    Test Acme client for wildard certificates.
    """

    # pylint: disable=E1125

    def setUp(self):
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
            self.client = sewer.client.Client(
                domain_name="*.exampleSTARcom",
                dns_class=self.dns_class,
                domain_alt_names=self.domain_alt_names,
                ACME_AUTH_STATUS_MAX_CHECKS=1,
                **usual_ACME(),
            )
        super(TestClientForWildcard, self).setUp()


class TestClientDnsApiCompatibility(TestCase):
    """
    Test Acme client support with the deprecated dns_class parameter.
    """

    # pylint: disable=E1125

    def setUp(self):
        self.domain_name = "example.com"
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.client.Client(
                domain_name=self.domain_name, dns_class=self.dns_class, **usual_ACME()
            )

    def test_get_get_acme_endpoints_failure_results_in_exception_with(self):
        with mock.patch(
            "requests.post", return_value=test_utils.MockResponse(status_code=409)
        ), mock.patch("requests.get", return_value=test_utils.MockResponse(status_code=409)):

            def mock_create_acme_client():
                sewer.client.Client(
                    domain_name="example.com",
                    dns_class=test_utils.ExmpleDnsProvider(),  # NOTE: dns_class used here
                    ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_STAGING,
                    LOG_LEVEL=LOG_LEVEL,
                    **keys_for_ACME(),
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
            self.client = sewer.client.Client(
                domain_name=self.domain_name,
                dns_class=self.dns_class,  # NOTE: dns_class used here
                domain_alt_names="domain_alt_names",
                **usual_ACME(),
            )

        with self.assertRaises(ValueError) as raised_exception:
            mock_instantiate_client()
        self.assertIn("None or a list of strings", str(raised_exception.exception))


class TestClientUnits(TestCase):

    # pylint: disable=E1125

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_args = {"domain_name": "example.com", "LOG_LEVEL": LOG_LEVEL}
        self.mock_args.update(keys_for_ACME())
        self.mock_challenges = [{"ident_value": "example.com", "key_auth": "abcdefgh12345678"}]

    def mock_sewer(self, provider):
        return sewer.client.Client(provider=provider, **self.mock_args)

    # sleep_iter is a prerequisite for the prop_timeout machinery

    def test01_sleep_iter_sticky(self):
        p = test_utils.ExmpleDNS(1, prop_sleep_times=[1, 2, 3, 4])
        sleep = self.mock_sewer(provider=p).sleep_iter()
        self.assertEqual([1, 2, 3, 4, 4, 4, 4, 4], [next(sleep) for i in range(8)])

    # prop_timeout mechanism (Client.propagation_delay)

    def test02_prop_timeout_okay(self):
        p = test_utils.ExmpleDNS(prop_timeout=1, fail_prop_count=0)
        self.mock_sewer(provider=p).propagation_delay(self.mock_challenges)

    def test03_prop_timeout_timeout(self):
        # with default [1,2,4,8] sleep times and timeout of 2, needs 3 failures to timeout
        p = test_utils.ExmpleDNS(prop_timeout=2, fail_prop_count=3)
        with self.assertRaises(RuntimeError):
            self.mock_sewer(provider=p).propagation_delay(self.mock_challenges)

    def test04_prop_timeout_delayed_okay(self):
        p = test_utils.ExmpleDNS(prop_timeout=20, fail_prop_count=2)
        self.mock_sewer(provider=p).propagation_delay(self.mock_challenges)
