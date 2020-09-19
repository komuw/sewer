from unittest import mock
from unittest import TestCase

from sewer.dns_providers.route53 import Route53Dns


class TestRoute53(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.route53_key_id = "mock-key-id"
        self.route53_key_secret = "mock-key-secret"
        self.dns_class = Route53Dns(self.route53_key_id, self.route53_key_secret)

    def tearDown(self):
        pass

    @staticmethod
    def mocked_route53_set_record_response():
        return {"ChangeInfo": {"Id": "mocked-id"}}

    def make_change_batch(self, action, domain_name, domain_value):
        return {
            "Comment": "certbot-dns-route53 certificate validation " + action,
            "Changes": [
                {
                    "Action": action,
                    "ResourceRecordSet": {
                        "Name": domain_name,
                        "Type": "TXT",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": domain_value}],
                    },
                }
            ],
        }

    def mocked_find_zone_response(self):
        return [
            {
                "HostedZones": [
                    {
                        "ResourceRecordSetCount": 3,
                        "CallerReference": "32621E71-EA83-B2E0-9C59-51126A25A3C3",
                        "Config": {"PrivateZone": False},
                        "Id": "/hostedzone/Z2EH0L5RFW3ACH",
                        "Name": "{}".format(self.domain_name),
                    }
                ],
                "IsTruncated": False,
                "ResponseMetadata": {
                    "RetryAttempts": 0,
                    "HTTPStatusCode": 200,
                    "RequestId": "09355760-92ea-456a-b64e-bdb0b2ff2bf1",
                    "HTTPHeaders": {
                        "x-amzn-requestid": "09355760-92ea-456a-b64e-bdb0b2ff2bf1",
                        "content-type": "text/xml",
                        "content-length": "3714",
                        "vary": "accept-encoding",
                        "date": "Wed, 04 Dec 2019 02:52:56 GMT",
                    },
                },
                "MaxItems": "100",
            }
        ]

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_user_given_credential(self, mock_client):
        dns_class = Route53Dns("mock-key", "mock-secret")
        mock_client.assert_called_once_with(
            "route53",
            aws_access_key_id="mock-key",
            aws_secret_access_key="mock-secret",
            config=dns_class.aws_config,
        )

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_user_given_client(self, mock_client):
        passed_client = mock.MagicMock()
        dns_class = Route53Dns(client=passed_client)
        mock_client.assert_not_called()
        self.assertEqual(passed_client, dns_class.r53)

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_user_given_creds_and_client(self, mock_client):
        with self.assertRaises(RuntimeError):
            Route53Dns(access_key_id="mock-key", client=mock.MagicMock())

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_user_not_given_credential(self, mock_client):
        dns_class = Route53Dns()
        mock_client.assert_called_once_with("route53", config=dns_class.aws_config)

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_route53_create_record(self, mock_client):
        dns_class = Route53Dns()
        # mock list zones paginator response
        mock_client.return_value.get_paginator.return_value.paginate.return_value = (
            self.mocked_find_zone_response()
        )
        mock_client.return_value.change_resource_record_sets.return_value = (
            self.mocked_route53_set_record_response()
        )

        change_id = dns_class.create_dns_record(self.domain_name, self.domain_dns_value)
        self.assertEqual(change_id, "mocked-id")

        mock_client.mock_calls[3].assert_called_once_with(
            HostedZoneId="mocked-id",
            ChangeBatch=self.make_change_batch("UPSERT", self.domain_name, self.domain_dns_value),
        )

    @mock.patch("sewer.dns_providers.route53.boto3.client")
    def test_route53_delete_record(self, mock_client):
        dns_class = Route53Dns()
        # mock list zones paginator response
        mock_client.return_value.get_paginator.return_value.paginate.return_value = (
            self.mocked_find_zone_response()
        )
        mock_client.return_value.change_resource_record_sets.return_value = (
            self.mocked_route53_set_record_response()
        )

        dns_class.create_dns_record(self.domain_name, self.domain_dns_value)
        dns_class.delete_dns_record(self.domain_name, self.domain_dns_value)

        mock_client.mock_calls[4].assert_called_once_with(
            HostedZoneId="mocked-id",
            ChangeBatch=self.make_change_batch("DELETE", self.domain_name, self.domain_dns_value),
        )
