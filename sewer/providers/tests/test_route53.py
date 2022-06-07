from unittest import mock
from unittest import TestCase

from sewer.providers.route53 import Route53Dns
from sewer.lib import dns_challenge


class TestRoute53(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.route53_key_id = "mock-key-id"
        self.route53_key_secret = "mock-key-secret"
        self.challenges = [{"ident_value": "example.com", "key_auth": "abcdefghijklmnop.0123456789"}]
        self.provider = Route53Dns(self.route53_key_id, self.route53_key_secret)

    def tearDown(self):
        pass

    @staticmethod
    def mocked_route53_set_record_response():
        return {"ChangeInfo": {"Id": "mocked-id"}}

    @staticmethod
    def mocked_route53_set_change_response():
        return {"ChangeInfo": {"Status": "INSYNC"}}

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

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_user_given_credential(self, mock_client):
        provider = Route53Dns("mock-key", "mock-secret")
        mock_client.assert_called_once_with(
            "route53",
            aws_access_key_id="mock-key",
            aws_secret_access_key="mock-secret",
            config=provider.aws_config,
        )

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_user_given_client(self, mock_client):
        passed_client = mock.MagicMock()
        provider = Route53Dns(client=passed_client)
        mock_client.assert_not_called()
        self.assertEqual(passed_client, provider.r53)

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_user_given_creds_and_client(self, mock_client):
        with self.assertRaises(RuntimeError):
            Route53Dns(access_key_id="mock-key", client=mock.MagicMock())

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_user_not_given_credential(self, mock_client):
        provider = Route53Dns()
        mock_client.assert_called_once_with("route53", config=provider.aws_config)

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_create_changeset(self, mock_client):
        provider = Route53Dns()
        mock_client.return_value.get_paginator.return_value.paginate.return_value = (
            self.mocked_find_zone_response()
        )
        changeset = provider._create_changeset_batches(self, self.challenges)
        self.assertEqual(
            changeset["/hostedzone/Z2EH0L5RFW3ACH"]["_acme-challenge.example.com"]["ResourceRecordSet"]["ResourceRecords"][0]["Value"],
            '"{0}"'.format(dns_challenge(self.challenges[0]["key_auth"]))
        )
    
    @mock.patch("sewer.providers.route53.boto3.client")
    def test_setup(self, mock_client):
        provider = Route53Dns()
        # mock list zones paginator response
        mock_client.return_value.get_paginator.return_value.paginate.return_value = (
            self.mocked_find_zone_response()
        )
        mock_client.return_value.change_resource_record_sets.return_value = (
            self.mocked_route53_set_record_response()
        )
        mock_client.return_value.get_change.return_value = (
            self.mocked_route53_set_change_response()
        )

        provider.setup(self.challenges)

        mock_client.mock_calls[3].assert_called_once_with(
            HostedZoneId="mocked-id",
            ChangeBatch=provider._create_changeset_batches("UPSERT", self.challenges)
        )

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_clear(self, mock_client):
        provider = Route53Dns()
        # mock list zones paginator response
        mock_client.return_value.get_paginator.return_value.paginate.return_value = (
            self.mocked_find_zone_response()
        )
        mock_client.return_value.change_resource_record_sets.return_value = (
            self.mocked_route53_set_record_response()
        )
        mock_client.return_value.get_change.return_value = (
            self.mocked_route53_set_change_response()
        )

        provider.clear(self.challenges)

        mock_client.mock_calls[3].assert_called_once_with(
            HostedZoneId="mocked-id",
            ChangeBatch=provider._create_changeset_batches("DELETE", self.challenges)
        )

    @mock.patch("sewer.providers.route53.boto3.client")
    def test_waiting_for_propagation(self, mock_client):
        provider = Route53Dns()

        mock_client.return_value.change_resource_record_sets.return_value = (
            self.mocked_route53_set_record_response()
        )
        mock_client.return_value.get_change.return_value = (
            self.mocked_route53_set_change_response()
        )

        changes = self.mocked_route53_set_record_response()
        provider._wait_for_propagation([changes["ChangeInfo"]["Id"]])

        mock_client.mock_calls[0].assert_called_once_with(
            Id=changes["ChangeInfo"]["Id"]
        )
