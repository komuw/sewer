from unittest import TestCase

import sewer


class TestCommon(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = 'example.com'
        self.domain_dns_value = 'wwfw2402if'
        self.dns_class = sewer.BaseDns()

    def tearDown(self):
        pass

    def test_create_dns_record(self):
        def mock_create_dns_record():
            self.dns_class.create_dns_record(
                domain_name=self.domain_name,
                domain_dns_value=self.domain_dns_value)
        self.assertRaises(NotImplementedError, mock_create_dns_record)

    def test_delete_dns_record(self):
        def mock_delete_dns_record():
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name,
                domain_dns_value=self.domain_dns_value)
        self.assertRaises(NotImplementedError, mock_delete_dns_record)
