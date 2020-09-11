import unittest

from .. import auth, catalog


class TestCatalog(unittest.TestCase):
    def test01_ProviderCatalog_create(self):
        cat = catalog.ProviderCatalog()
        self.assertIsInstance(cat, catalog.ProviderCatalog)

    def test02_catalog_get_item_list_okay(self):
        cat = catalog.ProviderCatalog()
        self.assertIsInstance(cat.get_item_list(), list)

    def test03_catalog_get_descriptor_okay(self):
        cat = catalog.ProviderCatalog()
        self.assertIsInstance(cat.get_descriptor("unbound_ssh"), catalog.ProviderDescriptor)

    def test04_catalog_get_provider_okay(self):
        cat = catalog.ProviderCatalog()
        provider = cat.get_provider("unbound_ssh")(ssh_des="noone@nowhere")
        self.assertIsInstance(provider, auth.ProviderBase)

    def test_05_catalog__str__okay(self):
        self.assertTrue(str(catalog.ProviderCatalog()))
