import unittest

from typing import Sequence, Tuple

from ..crypto import AcmeKey, AcmeCsr


KeyType = Tuple[str, int]


class Test_AcmeKey(unittest.TestCase):

    rsa_key_types = (("rsa2048", 2048), ("rsa3072", 3072), ("rsa4096", 4096))
    secp_key_types = (("secp256r1", 256), ("secp384r1", 384))

    def fromfile_privbytes_frombytes_sign_key(self, key_type: KeyType) -> None:
        """
        this has grown into a test for almost everything we do with keys
        """

        type_name, key_size = key_type
        filename = "test/%s.pem" % type_name

        # from_file
        loaded_key = AcmeKey.from_file(filename)
        self.assertTrue(loaded_key.pk.key_size == key_size)

        # private_bytes ("assert" no exception)
        loaded_pb = loaded_key.private_bytes()

        # private bytes matches original file
        with open(filename, "rb") as f:
            file_bytes = f.read()
        self.assertTrue(loaded_pb == file_bytes)

        # from_bytes
        reloaded_key = AcmeKey.from_bytes(loaded_pb)
        self.assertTrue(loaded_key.pk.private_numbers() == reloaded_key.pk.private_numbers())

        # sign_message
        self.assertTrue(len(loaded_key.sign_message(b"Taketh uth to thine leaderth")))

    def test11_rsa_kitchen_sink(self):
        for kt in self.rsa_key_types:
            self.fromfile_privbytes_frombytes_sign_key(kt)

    def test12_secp_kitchen_sink(self):
        for kt in self.secp_key_types:
            self.fromfile_privbytes_frombytes_sign_key(kt)

    def generate_test(self, key_types: Sequence[KeyType]) -> None:
        for type_name, key_size in key_types:
            key = AcmeKey.create(type_name)
            self.assertTrue(key.pk.key_size == key_size)

    def test21_generate_rsa_keys(self):
        self.generate_test(self.rsa_key_types)

    def test22_generate_ec_keys(self):
        self.generate_test(self.secp_key_types)


### TODO ### CSR tests
