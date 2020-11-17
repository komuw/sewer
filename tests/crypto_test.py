import unittest

from typing import Sequence, Tuple

from sewer.crypto import AcmeAccount, AcmeCsr, AcmeKey


KeyType = Tuple[str, int]

rsa_key_types = (("rsa2048", 2048), ("rsa3072", 3072), ("rsa4096", 4096))
secp_key_types = (("secp256r1", 256), ("secp384r1", 384))


def fromfile_privbytes_frombytes_sign_key(key_type: KeyType) -> None:
    """
    this has grown into a test for almost everything we do with keys
    """

    type_name, key_size = key_type
    filename = "tests/data/%s.pem" % type_name

    # read_pem
    loaded_key = AcmeKey.read_pem(filename)
    assert loaded_key.pk.key_size == key_size

    # to_pem ("assert" no exception)
    loaded_pb = loaded_key.to_pem()

    # to_pem matches original file
    with open(filename, "rb") as f:
        file_bytes = f.read()
    assert loaded_pb == file_bytes

    # from_pem
    reloaded_key = AcmeKey.from_pem(loaded_pb)
    assert loaded_key.pk.private_numbers() == reloaded_key.pk.private_numbers()

    # sign_message
    assert len(loaded_key.sign_message(b"Taketh uth to thine leaderth"))


def test11_rsa_kitchen_sink():
    for kt in rsa_key_types:
        fromfile_privbytes_frombytes_sign_key(kt)


def test12_secp_kitchen_sink():
    for kt in secp_key_types:
        fromfile_privbytes_frombytes_sign_key(kt)


def generate_test(key_types: Sequence[KeyType]) -> None:
    for type_name, key_size in key_types:
        key = AcmeKey.create(type_name)
        assert key.pk.key_size == key_size


def test21_generate_rsa_keys():
    generate_test(rsa_key_types)


def test22_generate_ec_keys():
    generate_test(secp_key_types)


def test31_read_key_write_acct_read_acct():
    acct = AcmeAccount.read_pem("tests/data/secp256r1.pem")
    assert isinstance(acct, AcmeAccount)
    test_kid = "https://acme-v02.api.letsencrypt.org/account/abc123def456ghi789"
    acct.kid = test_kid
    tmpfile = "tests/tmp/test31_acct_key.pem"
    acct.write_key(tmpfile)
    acct2 = AcmeAccount.read_key(tmpfile)
    assert acct2.kid == test_kid and acct2._timestamp == acct._timestamp


### TODO ### CSR tests
