import mock
import json
from unittest import TestCase

import sewer

from . import test_utils

import pprint

class TestRackspace(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = 'example.com'
        self.domain_dns_value = 'mock-domain_dns_value'
        self.RACKSPACE_USERNAME= 'mock_username'
        self.RACKSPACE_API_KEY = 'mock-api-key'
        self.RACKSPACE_API_TOKEN = 'mock-api-token'
        
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
            'requests.get') as mock_requests_get, mock.patch(
                    'sewer.RackspaceDns.get_rackspace_credentials') as mock_get_credentials, mock.patch(
                            'sewer.RackspaceDns.find_dns_zone_id', autospec=True) as mock_find_dns_zone_id:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            mock_get_credentials.return_value = 'mock-api-token', 'http://example.com/'
            mock_find_dns_zone_id.return_value = 'mock_zone_id'
            self.dns_class = sewer.RackspaceDns(
                RACKSPACE_USERNAME=self.RACKSPACE_USERNAME,
                RACKSPACE_API_KEY=self.RACKSPACE_API_KEY)

    def tearDown(self):
        pass

    def test_delete_dns_record_is_not_called_by_create_dns_record(self):
        with mock.patch('sewer.RackspaceDns.find_dns_zone_id') as mock_find_dns_zone_id, mock.patch(
                'requests.post') as mock_requests_post, mock.patch(
                    'requests.get') as mock_requests_get, mock.patch(
                        'requests.delete') as mock_requests_delete, mock.patch(
                            'sewer.RackspaceDns.delete_dns_record') as mock_delete_dns_record, mock.patch(
                                    'sewer.RackspaceDns.poll_callback_url') as mock_poll_callback_url:
                                mock_find_dns_zone_id.return_value = 'mock_zone_id'
                                mock_requests_get.return_value = \
                                    mock_requests_delete.return_value = \
                                    mock_delete_dns_record.return_value = test_utils.MockResponse()
                                mock_requests_content = {
                                        'callbackUrl': 'http://example.com/callbackUrl'
                                }
                                mock_requests_post.return_value = test_utils.MockResponse(202, mock_requests_content) 
                                mock_poll_callback_url.return_value = 1
                                self.dns_class.create_dns_record(
                                domain_name=self.domain_name,
                                domain_dns_value=self.domain_dns_value)
                                self.assertFalse(mock_delete_dns_record.called)

    def test_rackspace_is_called_by_create_dns_record(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'requests.delete') as mock_requests_delete, mock.patch(
                        'sewer.RackspaceDns.delete_dns_record') as mock_delete_dns_record, mock.patch(
                                'sewer.RackspaceDns.find_dns_zone_id') as mock_find_dns_zone_id, mock.patch(
                                        'sewer.RackspaceDns.poll_callback_url') as mock_poll_callback_url:
            mock_requests_content = {
                    'callbackUrl': 'http://example.com/callbackUrl'
            }
            mock_requests_post.return_value = test_utils.MockResponse(202, mock_requests_content)
            mock_requests_get.return_value = \
                mock_requests_delete.return_value = \
                mock_delete_dns_record.return_value = test_utils.MockResponse()
            mock_find_dns_zone_id.return_value = 'mock_zone_id'
            mock_poll_callback_url.return_value = 1

            self.dns_class.create_dns_record(
                domain_name=self.domain_name,
                domain_dns_value=self.
                domain_dns_value)
            expected = {
                    'headers' : {'X-Auth-Token': 'mock-api-token', 'Content-Type': 'application/json'},
                    'data': 'mock-domain_dns_value'}
            self.assertDictEqual(
                expected['headers'],
                mock_requests_post.call_args[1]['headers'])
            self.assertEqual(
                    expected['data'], mock_requests_post.call_args[1]['json']['records'][0]['data'])
           
    def test_rackspace_is_called_by_delete_dns_record(self):
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get, mock.patch(
                    'requests.delete') as mock_requests_delete, mock.patch(
                                'sewer.RackspaceDns.find_dns_zone_id') as mock_find_dns_zone_id, mock.patch(
                                        'sewer.RackspaceDns.poll_callback_url') as mock_poll_callback_url, mock.patch(
                                                'sewer.RackspaceDns.find_dns_record_id') as mock_find_dns_record_id:
            mock_requests_content = {
                    'callbackUrl': 'http://example.com/callbackUrl'
            }
            mock_requests_post.return_value = \
                mock_requests_get.return_value = test_utils.MockResponse()
            mock_requests_delete.return_value = test_utils.MockResponse(202, mock_requests_content)
            mock_find_dns_zone_id.return_value = 'mock_zone_id'
            mock_poll_callback_url.return_value = 1
            mock_find_dns_record_id.return_value = 'mock_record_id'

            self.dns_class.delete_dns_record(
                domain_name=self.domain_name,
                domain_dns_value=self.
                domain_dns_value)
            print('Karl')
            pprint.pprint(mock_requests_delete.call_args)
            print('Ended')
            expected = {
                    'headers' : {'X-Auth-Token': 'mock-api-token', 'Content-Type': 'application/json'},
                    'url': 'http://example.com/domains/mock_zone_id/records/?id=mock_record_id'}
            self.assertDictEqual(
                expected['headers'],
                mock_requests_delete.call_args[1]['headers'])
            self.assertEqual(
                    expected['url'], mock_requests_delete.call_args[0][0])
