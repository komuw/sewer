from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, utils
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

### FIX ME ### what can we use for XxxKeyType?  [[ not vital, just tightens up typing ]]

# RsaKeyType = openssl.rsa._RSAPrivateKey
# EcKeyType = openssl.ec._EllipticCurvePrivateKey
# AcmeKeyType = Union[RsaKeyType, EcKeyType]

# and why does this [seem] to work?
PrivateKeyType = Union[openssl.rsa._RSAPrivateKey, openssl.ec._EllipticCurvePrivateKey]


class AcmeKey:
    """
    AcmeKey is the base class for the actual type-specific classes.  It implements
    some common methods, usually in terms of class values or methods that only
    exist in the specific subclasses.

    NB: these are all wrappers and do NOT include key creation or loading.
    See new_ACME_key and load_ACME_key factory functions below.
    """

    def __init__(self, pk: PrivateKeyType) -> None:
        self.pk = pk
        # subclass dependent, assigned there
        self.private_format: Any
        self.jwk_const: Dict[str, str]
        self.jwk_attr: Dict[str, str]
        self.jws_alg: str
        # shared fields
        self.kid: Optional[str] = None
        self._jwk: Optional[Dict[str, str]] = None

    @staticmethod
    def create(key_type: str) -> "AcmeKey":
        """
        Factory method to create a new key of key_type, returned as an AcmeKey.
        """

        if key_type not in key_type_map:
            raise ValueError("AcmeKey.create: unrecognized key_type: %s" % key_type)
        Cls, arg = key_type_map[key_type]

        return Cls(Cls.create_pk(arg))

    @staticmethod
    def from_bytes(pem_data: bytes) -> "AcmeKey":
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
    def from_file(filename: str) -> "AcmeKey":
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

    ### TODO ### store & load file format with kid, PK, timestamp registered, ?

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
                numbytes = getattr(self, "jwk_num_bytes", (val.bit_length() + 7) // 8)
                jwk[name] = safe_base64(val.to_bytes(numbytes, "big"))
            self._jwk = jwk
        return self._jwk


### Concrete AcmeXxxKey classes

# NB: when adding a new key type, or extending one, remember to update key_type_map
# to match (below)


class AcmeRsaKey(AcmeKey):
    def __init__(self, pk: PrivateKeyType) -> None:
        super().__init__(pk)
        self.private_format = PrivateFormat.PKCS8
        self.jwk_const = {"kty": "RSA"}
        self.jwk_attr = {"e": "e", "n": "n"}
        self.jws_alg = "RS256"

    @staticmethod
    def create_pk(key_size: int) -> PrivateKeyType:
        return rsa.generate_private_key(65537, key_size, default_backend())

    def sign_message(self, message: bytes) -> bytes:
        """
        Yes, SHA256 is hardwired.  As of Sep 2020, LE only accepts that hash
        for RSA keys: "expected one of RS256, ES256, ES384 or ES512".
        """

        signature = self.pk.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return signature


class EcCurve:
    "data class to hold EX info that's not readily inferred from the secp### tag"

    def __init__(self, curve: Any, alg: str, hash_type: Any, nbytes: int) -> None:
        self.curve = curve
        self.alg = alg
        self.hash_type = hash_type
        self.nbytes = nbytes


known_curves: Dict[int, EcCurve] = {
    256: EcCurve(ec.SECP256R1, "ES256", hashes.SHA256, 32),
    384: EcCurve(ec.SECP384R1, "ES384", hashes.SHA384, 48),
    #
    # I thought LE accepted P-521 for account keys, but while chasing an intermitent bug
    # 'detail': 'ECDSA curve P-521 not allowed'
    #
    #    521: EcCurve(ec.SECP521R1, "ES512", hashes.SHA512, 66),
}


class AcmeEcKey(AcmeKey):
    def __init__(self, pk: PrivateKeyType) -> None:
        key_size = pk.curve.key_size
        info = known_curves[key_size]
        super().__init__(pk)
        self.private_format = PrivateFormat.PKCS8
        self.jwk_const = {"kty": "EC", "crv": "P-%s" % key_size}
        self.jwk_attr = {"x": "x", "y": "y"}
        self.jws_alg = info.alg

        self.jkw_num_bytes = info.nbytes

    @staticmethod
    def create_pk(key_size: int) -> PrivateKeyType:
        info = known_curves[key_size]
        return ec.generate_private_key(info.curve, default_backend())

    def sign_message(self, message: bytes) -> bytes:
        info = known_curves[self.pk.curve.key_size]
        # EC.sign returns ASN.1 encoded values for some inane reason
        r, s = utils.decode_dss_signature(self.pk.sign(message, ec.ECDSA(info.hash_type())))
        signature = r.to_bytes(info.nbytes, "big") + s.to_bytes(info.nbytes, "big")

        return signature


# key_type_map
# map known key type names to (concrete_class, key_size)

key_type_map: Dict[str, Tuple[Any, int]] = {
    "rsa2048": (AcmeRsaKey, 2048),
    "rsa3072": (AcmeRsaKey, 3072),
    "rsa4096": (AcmeRsaKey, 4096),
    "secp256r1": (AcmeEcKey, 256),
    "secp384r1": (AcmeEcKey, 384),
}

# extract just the names for option choice lists, etc.
key_type_choices = list(key_type_map)


### We also need to generate Certificate Signing Requests


class AcmeCsr:
    def __init__(self, *, cn: str, san: List[str], key: AcmeKey) -> None:
        """
        temporary "just like Client.create_csr", more or less

        TODO: "must staple" extension; NOT elaborating subject name, since LE
        suggests that even CN may be replaced by a meaningless number in some
        vague future version of the server.  I guess they're right that
        browsers ignore the CN already (aside from displaying it if asked).
        """

        csrb = x509.CertificateSigningRequestBuilder()
        csrb = csrb.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
        all_names = list(set([cn] + san))
        SAN: List[x509.GeneralName] = [x509.DNSName(name) for name in all_names]
        csrb = csrb.add_extension(x509.SubjectAlternativeName(SAN), critical=False)
        self.csr = csrb.sign(key.pk, hashes.SHA256(), default_backend())

    def public_bytes(self) -> bytes:
        return self.csr.public_bytes(Encoding.DER)
