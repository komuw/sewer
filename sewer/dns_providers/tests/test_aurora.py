import mock
from unittest import TestCase

import sewer

from . import test_utils


class TestAurora(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = 'example.com'
        self.base64_of_acme_keyauthorization = 'mock-base64_of_acme_keyauthorization'
        self.AURORA_API_KEY = 'mock-aurora-api-key'
        self.AURORA_SECRET_KEY = 'mock-aurora-secret-key'

        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = sewer.AuroraDns(
                AURORA_API_KEY=self.AURORA_API_KEY,
                AURORA_SECRET_KEY=self.AURORA_SECRET_KEY)

    def tearDown(self):
        pass

    def test_delete_dns_record_is_called_by_create_dns_record(self):
        with mock.patch(
                'sewer.dns_providers.auroradns.get_driver'
        ) as mock_get_driver, mock.patch(
                'requests.post') as mock_requests_post, mock.patch(
                    'requests.get') as mock_requests_get, mock.patch(
                        'requests.delete') as mock_requests_delete, mock.patch(
                            'sewer.AuroraDns.delete_dns_record'
                        ) as mock_delete_dns_record:
            mock_requests_post.return_value = \
                mock_requests_get.return_value = \
                mock_requests_delete.return_value = \
                mock_delete_dns_record.return_value = test_utils.MockResponse()
            mock_get_driver.return_value = test_utils.mockLibcloudGetDriver(
                'mock-provider')

            self.dns_class.create_dns_record(
                domain_name=self.domain_name,
                base64_of_acme_keyauthorization=self.
                base64_of_acme_keyauthorization)
            mock_delete_dns_record.assert_called_once_with(
                base64_of_acme_keyauthorization=self.
                base64_of_acme_keyauthorization,
                domain_name=self.domain_name)

    # def test_cloudflare_is_called_by_create_dns_record(self):
    #     with mock.patch('requests.post') as mock_requests_post, mock.patch(
    #             'requests.get') as mock_requests_get, mock.patch(
    #                 'requests.delete') as mock_requests_delete, mock.patch(
    #                     'sewer.CloudFlareDns.delete_dns_record'
    #                 ) as mock_delete_dns_record:
    #         mock_requests_post.return_value = \
    #             mock_requests_get.return_value = \
    #             mock_requests_delete.return_value = \
    #             mock_delete_dns_record.return_value = test_utils.MockResponse()

    #         self.dns_class.create_dns_record(
    #             domain_name=self.domain_name,
    #             base64_of_acme_keyauthorization=self.
    #             base64_of_acme_keyauthorization)
    #         expected = {
    #             'headers': {
    #                 'X-Auth-Email': self.CLOUDFLARE_EMAIL,
    #                 'X-Auth-Key': self.CLOUDFLARE_API_KEY,
    #                 'Content-Type': 'application/json'
    #             },
    #             'data':
    #             '{"content": "mock-base64_of_acme_keyauthorization", "type": "TXT", "name": "_acme-challenge.example.com."}',
    #             'timeout':
    #             65
    #         }

    #         self.assertDictEqual(expected, mock_requests_post.call_args[1])

    # def test_cloudflare_is_called_by_delete_dns_record(self):
    #     with mock.patch('requests.post') as mock_requests_post, mock.patch(
    #             'requests.get') as mock_requests_get, mock.patch(
    #                 'requests.delete') as mock_requests_delete:
    #         mock_requests_post.return_value = \
    #             mock_requests_delete.return_value = test_utils.MockResponse()

    #         mock_requests_get.return_value = test_utils.MockResponse(
    #             content="""{"result": [{"id": "some-id"}]}""")

    #         self.dns_class.delete_dns_record(
    #             domain_name=self.domain_name,
    #             base64_of_acme_keyauthorization=self.
    #             base64_of_acme_keyauthorization)

    #         self.assertTrue(mock_requests_get.called)
    #         expected = {
    #             'headers': {
    #                 'X-Auth-Email': self.CLOUDFLARE_EMAIL,
    #                 'X-Auth-Key': self.CLOUDFLARE_API_KEY,
    #                 'Content-Type': 'application/json'
    #             },
    #             'timeout': 65
    #         }
    #         self.assertDictEqual(expected, mock_requests_delete.call_args[1])
    #         self.assertIn(
    #             'https://some-mock-url.com/zones/mock-zone-id/dns_records/some-id',
    #             str(mock_requests_delete.call_args))
