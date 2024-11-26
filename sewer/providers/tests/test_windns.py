from unittest import TestCase
from unittest.mock import patch

from sewer.lib import SewerError
from sewer.providers.windns import WinDNS

ACME_CHALLENGE = "_acme-challenge"


class TestWinDNS(TestCase):
    def test_init_with_zone_provided(self):
        def _fn():
            zone = "example.com"
            provider = WinDNS(zone)
            self.assertIsNotNone(provider)

        run_test_with_common_mocking(_fn)

    def test_init_with_zone_missing(self):
        def _fn():
            with self.assertRaisesRegex(
                ValueError, "windns requires a string value for the zone argument"
            ):
                WinDNS()

        run_test_with_common_mocking(_fn)

    def test_init_module_is_installed(self):
        run_test_with_common_mocking(lambda: WinDNS("example.com"))

    def test_init_module_is_not_installed(self):
        def _fn():
            with self.assertRaisesRegex(
                SewerError, "It seems that, the DNSServer module is not installed"
            ):
                WinDNS("example.com")

        run_test_with_common_mocking(_fn, False)

    def test_validate_domain_contains_zone(self):
        def _fn():
            mock_challenge = _mock_challenge_1()
            mock_zone = "example.com"

            provider = WinDNS(mock_zone)
            provider._validate_domain_contains_zone(mock_challenge)

        run_test_with_common_mocking(_fn)

    def test_assert_domain_missing_zone(self):
        def _fn():
            mock_challenge = _mock_challenge_1()
            mock_zone = "missing_zone"

            provider = WinDNS(mock_zone)

            with self.assertRaisesRegex(SewerError, "Domain must contains zone, domain"):
                provider._validate_domain_contains_zone(mock_challenge)

        run_test_with_common_mocking(_fn)

    def test_extract_sub_domain(self):
        def _test1():
            mock_challenge = _mock_challenge_1()
            mock_zone = "example.com"

            provider = WinDNS(mock_zone)
            dns_name = provider._extract_sub_domain_from_challenge(mock_challenge)

            self.assertEqual(dns_name, ACME_CHALLENGE)

        def _test2():
            mock_challenge = _mock_challenge_2()
            mock_zone = "example.com"

            provider = WinDNS(mock_zone)

            dns_name = provider._extract_sub_domain_from_challenge(mock_challenge)

            self.assertEqual(dns_name, "%s.test" % ACME_CHALLENGE)

        run_test_with_common_mocking(_test1)

    def test_alias_domain(self):
        def _fn():
            mock_challenge = _mock_challenge_1()
            mock_alias = "alias.com"
            mock_alias_zone = mock_alias

            provider = WinDNS(mock_alias_zone, alias=mock_alias)

            dns_name = provider._extract_sub_domain_from_challenge(mock_challenge)

            mock_domain = mock_challenge["ident_value"]
            self.assertEqual(dns_name, mock_domain)

        run_test_with_common_mocking(_fn)


def run_test_with_common_mocking(fn, is_module_installed=True):
    with patch(
        "windowsdnsserver.dns.dnsserver.DnsServerModule.is_dns_server_module_installed"
    ) as mock_module_installed, patch("platform.system") as mock_platform:
        mock_module_installed.return_value = is_module_installed
        mock_platform.return_value = "Windows"

        fn()


def _mock_challenge_1():
    return {"ident_value": "example.com"}


def _mock_challenge_2():
    return {"ident_value": "test.example.com"}
