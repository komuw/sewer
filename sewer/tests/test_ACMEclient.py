# the test dir is a sub dir of sewer/sewer so as
# not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import mock
from unittest import TestCase

import sewer

from . import test_utils


class TestACMEclient(TestCase):

    def setUp(self):
        self.domain_name = 'example.com'
        with mock.patch('requests.post') as mock_requests_post, mock.patch(
                'requests.get') as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class = test_utils.ExmpleDnsProvider()
            self.client = sewer.Client(
                domain_name=self.domain_name, dns_class=self.dns_class)

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


# from unittest import TestCase
# from funniest.command_line import main

# class TestConsole(TestCase):
#     def test_basic(self):
#         main()
