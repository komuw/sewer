import unittest

from .. import demo


class TestDemo(unittest.TestCase):
    "this actually tests nothing non-trivial, just exercises various code paths."

    def test_create_dns(self):
        p = demo.ManualProvider(chal_type="dns-01")
        self.assertTrue(p)

    def test_create_http(self):
        p = demo.ManualProvider(chal_type="http-01")
        self.assertTrue(p)

    def test_create_invalid(self):
        "like this: tests one out of an infinity of invalid values.  but 'covers' the exception"

        with self.assertRaises(ValueError):
            demo.ManualProvider(chal_type="invalid-01")

    def test_run_dns(self):
        p = demo.ManualProvider(chal_type="dns-01")
        self.assertFalse(
            p.setup([{"ident_value": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}])
            or p.unpropagated(
                [{"ident_value": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}]
            )
            or p.clear(
                [{"ident_value": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}]
            )
        )

    def test_run_http(self):
        p = demo.ManualProvider(chal_type="http-01")
        self.assertFalse(
            p.setup([{"token": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}])
            or p.unpropagated(
                [{"token": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}]
            )
            or p.clear([{"token": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}])
        )

    def test_accept_empty_chal_list(self):
        p = demo.ManualProvider(chal_type="http-01")
        self.assertFalse(p.setup([]) or p.unpropagated([]) or p.clear([]))

    def test_fails_dns_bad_chal(self):
        p = demo.ManualProvider(chal_type="dns-01")
        with self.assertRaises(KeyError):
            p.setup([{"token": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}])

    def test_fails_http_bad_chal(self):
        p = demo.ManualProvider(chal_type="http-01")
        with self.assertRaises(KeyError):
            p.setup([{"ident_value": "www.example.com", "key_auth": "abcdefghijklmnop.0123456789"}])
