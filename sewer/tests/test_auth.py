import unittest

from .. import auth, lib


def pbj(**kwargs):
    return auth.ProviderBase(chal_types=["dns-01"], **kwargs)


class TestAuth01(unittest.TestCase):
    "tests of __init__"

    ### probing the required parameter - chal_types

    def test01_requires_chal_types(self):
        with self.assertRaises(TypeError):
            auth.ProviderBase()  # pylint: disable=E1125

    def test02_accepts_valid_chal_types(self):
        chal_types = (["dns-01"], ["dns-01", "http-01"], ("dns-01",), ("dns-01", "http-01"))
        for ct in chal_types:
            with self.subTest(ct=ct):
                self.assertTrue(auth.ProviderBase(chal_types=ct))

    def _rejects_invalid_value_chal_types(self, chal_types):
        with self.assertRaises(ValueError):
            auth.ProviderBase(chal_types=chal_types)

    def test03_rejects_str_chal_types(self):
        self._rejects_invalid_value_chal_types("naked string is most likely error")

    def test04_rejects_iter_chal_types(self):
        self._rejects_invalid_value_chal_types(iter(["dns-01", "http-01"]))

    ### quick check for handling of unrecognized or surplus parameters

    def test05_rejects_unknown_parameters(self):
        with self.assertRaises(TypeError):
            pbj(jelly="strawberry")

    ### optional, one but not both -  logger and LOG_LEVEL parameters?

    def test06_accepts_logger(self):
        self.assertTrue(pbj(logger=lib.create_logger("", "INFO")))

    def test07_accepts_log_level(self):
        self.assertTrue(pbj(LOG_LEVEL="INFO"))

    # current implementation allows both parameters :-(
    @unittest.expectedFailure
    def test08_rejects_logger_and_log_level(self):
        with self.assertRaises(ValueError):
            pbj(logger=lib.create_logger("", "INFO"), LOG_LEVEL="INFO")

    ### optional prop_timeout, prop_sleep_times

    def test09_prop_timeout_and_times_default(self):
        p = auth.ProviderBase(chal_types=["dns-01"])
        self.assertEqual(p.prop_timeout, 0)
        self.assertEqual(p.prop_sleep_times, (1, 2, 4, 8))

    def test10_prop_timeout_accepted(self):
        self.assertEqual(pbj(prop_timeout=30).prop_timeout, 30)

    def test11_prop_sleep_times_int_accepted(self):
        self.assertEqual(pbj(prop_sleep_times=4).prop_sleep_times, (4,))

    def test12_prop_sleep_times_list_accepted(self):
        self.assertEqual(pbj(prop_sleep_times=[2, 4, 6, 8, 10]).prop_sleep_times, (2, 4, 6, 8, 10))

    def test13_prop_sleep_times_tuple_accepted(self):
        self.assertEqual(pbj(prop_sleep_times=(2, 4, 6, 8, 10)).prop_sleep_times, (2, 4, 6, 8, 10))

    def test14_prop_sleep_times_rejects(self):
        with self.assertRaises(ValueError):
            pbj(prop_sleep_times=[1, "b", 4, 8])


class TestAuth02(unittest.TestCase):
    "tests of abstract methods"

    def test01_notimplemented_setup(self):
        with self.assertRaises(NotImplementedError):
            pbj().setup([{}])

    def test02_notimplemented_unpropagated(self):
        with self.assertRaises(NotImplementedError):
            pbj().unpropagated([{}])

    def test03_notimplemented_clear(self):
        with self.assertRaises(NotImplementedError):
            pbj().clear([{}])


class TestAuthHTTP(unittest.TestCase):
    "tests for the new-model HTTP sub-base class"

    def test01_requires_nothing(self):
        self.assertTrue(auth.HTTPProviderBase())

    def test02_accepts_chal_types(self):
        self.assertTrue(auth.HTTPProviderBase(chal_types=["http-01"]))


class TestAuthDNS(unittest.TestCase):
    "tests for the new-model DNS sub-base class"

    def test01_requires_nothing(self):
        self.assertTrue(auth.DNSProviderBase())

    def test02_accepts_chal_types(self):
        self.assertTrue(auth.DNSProviderBase(chal_types=["dns-01"]))

    def test03_accepts_alias(self):
        self.assertTrue(auth.DNSProviderBase(alias="dns-01"))

    def test04_without_alias(self):
        p = auth.DNSProviderBase()
        chal = {"ident_value": "example.com"}
        self.assertTrue(
            p.cname_domain(chal) is None and p.target_domain(chal) == "_acme-challenge.example.com"
        )

    def test05_with_alias(self):
        p = auth.DNSProviderBase(alias="valid.com")
        chal = {"ident_value": "example.com"}
        self.assertTrue(
            p.target_domain(chal) == "example.com.valid.com"
            and p.cname_domain(chal) == "_acme-challenge.example.com"
        )
