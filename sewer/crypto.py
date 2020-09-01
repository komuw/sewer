from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from cryptography.hazmat.backends import default_backend, openssl

from typing import Any, Dict, List, Optional, Tuple, Union

from .lib import safe_base64


### types for things defined here

### FIX ME ### what can we use for XxxKeyType?

# RsaKeyType = openssl.rsa._RSAPrivateKey
# EcKeyType = openssl.ec._EllipticCurvePrivateKey
# AcmeKeyType = Union[RsaKeyType, EcKeyType]

# and why does this [seem] to work?
AcmeKeyType = Union[openssl.rsa._RSAPrivateKey, openssl.ec._EllipticCurvePrivateKey]


class AcmeKey:
    """
    AcmeKey is the base class for the actual type-specific classes.  It implements
    some common methods, usually in terms of class values or methods that only
    exist in the specific subclasses.

    NB: these are all wrappers and do NOT include key creation or loading.
    See new_ACME_key and load_ACME_key factory functions below.
    """

    pk: AcmeKeyType

    private_format: Any = None
    jwk_const: Dict[str, str]
    jwk_attr: Dict[str, str]

    def __init__(self, pk: AcmeKeyType) -> None:
        self.pk = pk
        self.kid: Optional[str] = None
        self._jwk: Optional[Dict[str, str]] = None

    @staticmethod
    def create(key_type: str) -> AcmeKeyType:
        """
        Factory method to create a new key of key_type, returned as an AcmeKey.
        """

        if key_type not in key_type_map:
            raise ValueError("AcmeKey.create: unrecognized key_type: %s" % key_type)
        Cls, arg = key_type_map[key_type]

        # ? # I suppose this could be inverted to keep the key type specifics in Cls

        if Cls is AcmeRsaKey:
            return Cls(rsa.generate_private_key(65537, arg, default_backend()))
        if Cls is AcmeEcKey:
            return Cls(ec.generate_private_key(arg, default_backend()))

        raise ValueError("AcmeKey.create: got bad class from type_map")

    @staticmethod
    def from_bytes(pem_data: bytes) -> AcmeKeyType:
        """
        load a key from the PEM-format bytes, return an AcmeKey

        NB: since it's not stored in the PEM, the kid is empty (None)
        """

        pk = load_pem_private_key(pem_data, None, default_backend())

        if isinstance(pk, rsa.RSAPrivateKey):
            return AcmeRsaKey(pk)
        if isinstance(pk, ec.EllipticCurvePrivateKey):
            return AcmeEcKey(pk)

        raise ValueError("AcmeKey.from_bytes: unrecognized key type: %s" % pk)

    @staticmethod
    def from_file(filename: str) -> AcmeKeyType:
        "convenience method to load a PEM-format key; returns the AcmeKey"

        with open(filename, "rb") as f:
            return AcmeKey.from_bytes(f.read())

    def set_kid(self, kid: str) -> None:
        """
        The kid is received when registering the key with the ACME service
        """
        self.kid = kid

    def private_bytes(self) -> bytes:
        """
        return pk's serialized (PEM) form

        USES ConcreteClass.private_format
        """

        pem_data = self.pk.private_bytes(
            encoding=Encoding.PEM, format=self.private_format, encryption_algorithm=NoEncryption()
        )
        return pem_data

    def to_file(self, filename: str) -> None:
        "convenience method to write out the key in PEM form"

        with open(filename, "wb") as f:
            f.write(self.private_bytes())

    def sign_message(self, message: bytes) -> bytes:
        raise NotImplementedError("subclass must implement sign_message")

    def jwk(self) -> Dict[str, str]:
        """
        Returns the key's JWK as a dictionary

        CACHES result in _jwk

        USES ConcreteClass.{jwk_const, jwk_attr}
        """

        if not self._jwk:
            pubnums = self.pk.public_key().public_numbers()
            jwk = dict(self.jwk_const)  # pylint: disable=E1101
            for name, attr_name in self.jwk_attr.items():  # pylint: disable=E1101
                val = getattr(pubnums, attr_name)
                numbytes = (val.bit_length() + 7) // 8
                jwk[name] = safe_base64(val.to_bytes(numbytes, "big"))
            self._jwk = jwk
        return self._jwk


### Concrete AcmeXxxKey classes

# NB: when adding a new key type, or extending one, remember to update key_type_map
# to match (below)


class AcmeRsaKey(AcmeKey):

    # maybe TraditionalOpenSSL to come out the same as testdata keys?
    private_format = PrivateFormat.PKCS8
    jwk_const = {"kty": "RSA"}
    jwk_attr = {"e": "e", "n": "n"}

    def sign_message(self, message: bytes) -> bytes:
        signature = self.pk.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return signature


class AcmeEcKey(AcmeKey):

    private_format = PrivateFormat.TraditionalOpenSSL
    # jwk_const has to be set based on the key size
    jwk_attr = {"x": "x", "y": "y"}

    def __init__(self, pk: AcmeKeyType) -> None:
        self.jwk_const = {"kty": "EC", "crv": "P-%s" % pk.curve.key_size}
        super().__init__(pk)

    def sign_message(self, message: bytes) -> bytes:
        signature = self.pk.sign(message, ec.ECDSA(hashes.SHA256()))
        return signature


# Key Type Registry
#
# key_type_map - maps key type name to the AcmeKey subclass that handles it and
# some magic values that are arguments needed for creating a new key.

key_type_map: Dict[str, Tuple[Any, ...]] = {
    "rsa2048": (AcmeRsaKey, 2048),
    "rsa3072": (AcmeRsaKey, 3072),
    "rsa4096": (AcmeRsaKey, 4096),
    "secp256r1": (AcmeEcKey, ec.SECP256R1),
    "secp384r1": (AcmeEcKey, ec.SECP384R1),
    "secp521r1": (AcmeEcKey, ec.SECP521R1),
}

# extract just the names for option choice lists, etc.
key_type_choices = list(key_type_map)


### We also need to generate Certificate Signing Requests


class AcmeCsr:
    def __init__(self, *, cn: str, san: List[str], key: AcmeKey) -> None:
        """
        temporary "just like Client.create_csr", more or less
        """

        csrb = x509.CertificateSigningRequestBuilder()
        csrb = csrb.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
        all_names = list(set([cn] + san))
        SAN: List = [x509.DNSName(name) for name in all_names]
        csrb = csrb.add_extension(x509.SubjectAlternativeName(SAN), critical=False)
        self.csr = csrb.sign(key.pk, hashes.SHA256(), default_backend())

    def public_bytes(self) -> bytes:
        return self.csr.public_bytes(Encoding.DER)
