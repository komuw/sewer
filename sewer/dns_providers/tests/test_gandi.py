from unittest import mock
from unittest import TestCase

import sewer

MOCK_GANDI_API_KEY = "gandi-Api-Key"


class MockResponseObject:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


def add_side_effect_to_request_get(mock_requests_get):
    def mock_implementation(*args, **kwargs):
        if (
            args[0]
            == "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld"
        ):
            return MockResponseObject(
                body={"zone_records_href": "mock_zone_records_href"}
            )

        if args[0] == "mock_zone_records_href":
            return MockResponseObject(
                body=[
                    {
                        "rrset_href": "mock_record_href",
                        "rrset_type": "TXT",
                        "rrset_ttl": 10800,
                        "rrset_name": "_acme-challenge.subsubdomain.subdomain",
                        "rrset_values": ["challenge_text"],
                    }
                ]
            )

        return MockResponseObject(status_code=404)

    mock_requests_get.side_effect = mock_implementation


def add_side_effect_to_request_post(mock_requests_post):
    def mock_implementation(*args, **kwargs):
        if args[0] == "mock_zone_records_href":
            return MockResponseObject()

        return MockResponseObject(status_code=404)

    mock_requests_post.side_effect = mock_implementation


def add_side_effect_to_request_delete(mock_requests_delete):
    def mock_implementation(*args, **kwargs):
        if args[0] == "mock_record_href":
            return MockResponseObject()

        return MockResponseObject(status_code=404)

    mock_requests_delete.side_effect = mock_implementation


@mock.patch("requests.delete")
@mock.patch("requests.post")
@mock.patch("requests.get")
def mock_requests(func, mock_requests_get, mock_requests_post, mock_requests_delete):
    class MockRequests:
        def __init__(self, mock_get, mock_post, mock_delete):
            self.get = mock_get
            self.post = mock_post
            self.delete = mock_delete

    def add_mock_implementations():
        add_side_effect_to_request_get(mock_requests_get)
        add_side_effect_to_request_post(mock_requests_post)
        add_side_effect_to_request_delete(mock_requests_delete)

    def inner(*args, **kwargs):
        mock_requests_lib = MockRequests(
            mock_requests_get, mock_requests_post, mock_requests_delete
        )
        return func(*[*args, mock_requests_lib], **kwargs)

    add_mock_implementations()
    return inner


class TestGandiDns(TestCase):

    EXPECTED_GET_HEADERS = {"X-Api-Key": MOCK_GANDI_API_KEY}

    EXPECTED_POST_HEADERS = {
        "X-Api-Key": MOCK_GANDI_API_KEY,
        "Content-Type": "application/json",
    }

    def check_correct_headers_passed(self, calls, expectedHeaders):
        for call in calls:
            self.assertEqual(call[1]["headers"], expectedHeaders)

    @mock_requests
    def test_delete_existing_record(self, mock_requests_lib):
        gandi_dns = sewer.GandiDns(
            GANDI_API_KEY=MOCK_GANDI_API_KEY, requests_lib=mock_requests_lib
        )
        gandi_dns.delete_dns_record(
            "subsubdomain.subdomain.second-level-domain.tld", "val"
        )

        get_calls = mock_requests_lib.get.call_args_list
        delete_calls = mock_requests_lib.delete.call_args_list

        self.check_correct_headers_passed(get_calls, TestGandiDns.EXPECTED_GET_HEADERS)
        self.check_correct_headers_passed(
            delete_calls, TestGandiDns.EXPECTED_GET_HEADERS
        )

        self.assertEqual(
            get_calls[0][0][0],
            "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld",
        )
        self.assertEqual(get_calls[1][0][0], "mock_zone_records_href")
        self.assertEqual(delete_calls[0][0][0], "mock_record_href")

    @mock_requests
    def test_delete_non_existing_record(self, mock_requests_lib):
        gandi_dns = sewer.GandiDns(
            GANDI_API_KEY=MOCK_GANDI_API_KEY, requests_lib=mock_requests_lib
        )
        with self.assertRaises(RuntimeError) as context:
            gandi_dns.delete_dns_record("no-exist.second-level-domain.tld", "val")

        self.assertEqual(
            "there is not exactly one record for domain: no-exist.second-level-domain.tld",
            str(context.exception),
        )

    @mock_requests
    def test_create_record(self, mock_requests_lib):
        gandi_dns = sewer.GandiDns(
            GANDI_API_KEY=MOCK_GANDI_API_KEY, requests_lib=mock_requests_lib
        )
        gandi_dns.create_dns_record(
            "subsubdomain.subdomain.second-level-domain.tld", "val"
        )

        get_calls = mock_requests_lib.get.call_args_list
        post_calls = mock_requests_lib.post.call_args_list
        delete_calls = mock_requests_lib.delete.call_args_list

        self.check_correct_headers_passed(get_calls, TestGandiDns.EXPECTED_GET_HEADERS)
        self.check_correct_headers_passed(
            post_calls, TestGandiDns.EXPECTED_POST_HEADERS
        )
        self.check_correct_headers_passed(
            delete_calls, TestGandiDns.EXPECTED_GET_HEADERS
        )

        self.assertEqual(
            get_calls[0][0][0],
            "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld",
        )
        self.assertEqual(get_calls[1][0][0], "mock_zone_records_href")
        self.assertEqual(delete_calls[0][0][0], "mock_record_href")

        self.assertEqual(
            get_calls[2][0][0],
            "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld",
        )
        self.assertEqual(post_calls[0][0][0], "mock_zone_records_href")
        self.assertEqual(post_calls[0][1]["json"]["rrset_type"], "TXT")
        self.assertEqual(post_calls[0][1]["json"]["rrset_ttl"], 10800)
        self.assertEqual(
            post_calls[0][1]["json"]["rrset_name"],
            "_acme-challenge.subsubdomain.subdomain",
        )
        self.assertEqual(post_calls[0][1]["json"]["rrset_values"], ["val"])

    @mock_requests
    def test_create_non_existing_record(self, mock_requests_lib):
        gandi_dns = sewer.GandiDns(
            GANDI_API_KEY=MOCK_GANDI_API_KEY, requests_lib=mock_requests_lib
        )
        gandi_dns.create_dns_record("subdomain.second-level-domain.tld", "val")

        get_calls = mock_requests_lib.get.call_args_list
        post_calls = mock_requests_lib.post.call_args_list
        delete_calls = mock_requests_lib.delete.call_args_list

        self.check_correct_headers_passed(get_calls, TestGandiDns.EXPECTED_GET_HEADERS)
        self.check_correct_headers_passed(
            post_calls, TestGandiDns.EXPECTED_POST_HEADERS
        )
        self.check_correct_headers_passed(
            delete_calls, TestGandiDns.EXPECTED_GET_HEADERS
        )

        self.assertEqual(
            get_calls[0][0][0],
            "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld",
        )
        self.assertEqual(get_calls[1][0][0], "mock_zone_records_href")
        self.assertEqual(len(delete_calls), 0)

        self.assertEqual(
            get_calls[2][0][0],
            "https://dns.api.gandi.net/api/v5/domains/second-level-domain.tld",
        )
        self.assertEqual(post_calls[0][0][0], "mock_zone_records_href")
        self.assertEqual(post_calls[0][1]["json"]["rrset_type"], "TXT")
        self.assertEqual(post_calls[0][1]["json"]["rrset_ttl"], 10800)
        self.assertEqual(
            post_calls[0][1]["json"]["rrset_name"], "_acme-challenge.subdomain"
        )
        self.assertEqual(post_calls[0][1]["json"]["rrset_values"], ["val"])
