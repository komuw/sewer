import logging
import unittest

from .. import lib


class response:
    def __init__(self, *, content_val="", json_val=None):
        self.content = content_val
        self._json = json_val

    def json(self):
        if self._json is None:
            raise ValueError("No json here")
        return self._json


class TestLib(unittest.TestCase):
    def test01_log_response_json_okay(self):
        self.assertEqual(lib.log_response(response(json_val="{}")), "{}")

    def test02_log_response_content_okay(self):
        self.assertEqual(lib.log_response(response(content_val="{}")), "{}")

    def test11_create_logger_okay(self):
        logger = lib.create_logger("silly_test_logger", 42)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.getEffectiveLevel(), 42)
        self.assertTrue(logger.hasHandlers())

    def test21_safe_base64_str_or_bytes_okay(self):
        self.assertIsInstance(lib.safe_base64("test string"), str)
        self.assertIsInstance(lib.safe_base64(b"test bytes"), str)

    def test31_dns_challenge_okay(self):
        res = lib.dns_challenge("a most spurious and unlikely key auth string")
        self.assertEqual(res, "lNNwvD6ceN7n6Iugd3m3k6HQD8Wk6ytGvKkwhHAV_Hw")
