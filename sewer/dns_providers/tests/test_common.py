from unittest import mock, TestCase

import sewer.dns_providers.common


class TestCommon(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "wwfw2402if"
        self.challenges = [{"ident_value": "example.com", "key_auth": "abcdefgh12345678"}]
        self.dns_class = sewer.dns_providers.common.BaseDns()

    def tearDown(self):
        pass

    def test_create_dns_record(self):
        def mock_create_dns_record():
            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

        self.assertRaises(NotImplementedError, mock_create_dns_record)

    def test_delete_dns_record(self):
        def mock_delete_dns_record():
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

        self.assertRaises(NotImplementedError, mock_delete_dns_record)

    def test_setup_empty(self):
        self.assertFalse(self.dns_class.setup([]))

    def test_clear_empty(self):
        self.assertFalse(self.dns_class.clear([]))

    def test_setup_mocked(self):
        with mock.patch("sewer.dns_providers.common.BaseDns.create_dns_record") as cdr:
            self.dns_class.setup(self.challenges)
            self.assertTrue(cdr.called)

    def test_clear_mocked(self):
        with mock.patch("sewer.dns_providers.common.BaseDns.delete_dns_record") as ddr:
            self.dns_class.clear(self.challenges)
            self.assertTrue(ddr.called)
