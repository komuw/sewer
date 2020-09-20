import time

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

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .lib import AcmeError, safe_base64


### Exceptions specific to ACME crypto operations


class AcmeKeyError(AcmeError):
    pass


class AcmeKeyTypeError(AcmeError):
    pass


class AcmeKidError(AcmeKeyError):
    pass


### types for things defined here

### FIX ME ### what can we use for XxxKeyType?  [[ not vital, just tightens up typing ]]

# RsaKeyType = openssl.rsa._RSAPrivateKey
# EcKeyType = openssl.ec._EllipticCurvePrivateKey
# AcmeKeyType = Union[RsaKeyType, EcKeyType]

# and why does this [seem] to work?
PrivateKeyType = Union[openssl.rsa._RSAPrivateKey, openssl.ec._EllipticCurvePrivateKey]


### low level key type table


class KeyDesc:
    def __init__(
        self,
        type_name: str,
        generate: Callable,
        gen_arg,
        pk_type,
        sign: Callable,
        sign_kwargs: Dict[str, Any],
        jwk: Dict[str, Any],
    ) -> None:
        self.type_name = type_name
        self.generate = generate
        self.gen_arg = gen_arg
        self.pk_type = pk_type
        self.sign = sign
        self.sign_kwargs = sign_kwargs
        self.jwk = jwk

    def _size(self) -> int:
        if isinstance(self.gen_arg, int):
            return self.gen_arg
        # else gen_arg is ec.SECP###R1
        return self.gen_arg.key_size

    def match(self, pk: PrivateKeyType) -> bool:
        if isinstance(pk, self.pk_type) and pk.key_size == self._size():
            return True
        return False


def rsa_gen(key_size: int) -> PrivateKeyType:
    return rsa.generate_private_key(65537, key_size, default_backend())


def ec_gen(curve) -> PrivateKeyType:
    return ec.generate_private_key(curve, default_backend())


def rsa_sign(pk, message: bytes) -> bytes:
    "Yes, SHA256 is hardwired.  As of Sep 2020, LE rejects other hashes for RSA"

    return pk.sign(message, padding.PKCS1v15(), hashes.SHA256())


def ec_sign(pk, message: bytes, *, hash_type, nbytes: int) -> bytes:
    # EC sign method returns ASN.1 encoded values for some inane reason
    r, s = utils.decode_dss_signature(pk.sign(message, ec.ECDSA(hash_type())))
    return r.to_bytes(nbytes, "big") + s.to_bytes(nbytes, "big")


key_table = [
    KeyDesc(
        "rsa2048",
        rsa_gen,
        2048,
        rsa.RSAPrivateKey,
        rsa_sign,
        {},
        {"const": {"kty": "RSA"}, "attrib": {"e": "e", "n": "n"}, "alg": "RS256", "nbytes": 0},
    ),
    KeyDesc(
        "rsa3072",
        rsa_gen,
        3072,
        rsa.RSAPrivateKey,
        rsa_sign,
        {},
        {"const": {"kty": "RSA"}, "attrib": {"e": "e", "n": "n"}, "alg": "RS256", "nbytes": 0},
    ),
    KeyDesc(
        "rsa4096",
        rsa_gen,
        4096,
        rsa.RSAPrivateKey,
        rsa_sign,
        {},
        {"const": {"kty": "RSA"}, "attrib": {"e": "e", "n": "n"}, "alg": "RS256", "nbytes": 0},
    ),
    KeyDesc(
        "secp256r1",
        ec_gen,
        ec.SECP256R1,
        ec.EllipticCurvePrivateKey,
        ec_sign,
        {"hash_type": hashes.SHA256, "nbytes": 32},
        {
            "const": {"kty": "EC", "crv": "P-256"},
            "attrib": {"x": "x", "y": "y"},
            "alg": "ES256",
            "nbytes": 32,
        },
    ),
    KeyDesc(
        "secp384r1",
        ec_gen,
        ec.SECP384R1,
        ec.EllipticCurvePrivateKey,
        ec_sign,
        {"hash_type": hashes.SHA384, "nbytes": 48},
        {
            "const": {"kty": "EC", "crv": "P-384"},
            "attrib": {"x": "x", "y": "y"},
            "alg": "ES384",
            "nbytes": 48,
        },
    ),
]

# extract just the names for option choice lists, etc.
key_type_choices = [kd.type_name for kd in key_table]


### AcmeKey, finally!


class AcmeKey:
    """
    AcmeKey is a parameterized wrapper around the private key type that are
    useful with ACME services.  Key creation, loading and storing, message
    signing, and generating the key's JWK are all provided.  Only key creation
    needs to be told the kind or size of key, and other differences in these
    operations are hidden away.

    See the key_table (or key_type_choices if you just want a list of the
    valid type names for the create method ( eg., sewer's cli program).

    These are based on what Let's Encrypt's servers accept as of Sep 2020:
    RSA with SHA256, P-256 with SHA256, and P-384 with SHA384.  LE doubtless
    accepts many other key sizes than our simple list-based setup provides,
    but these are the ones sewer has actually tested (which is how we found
    out that RSA was SHA256 only, and P-521 wasn't available at all).  Of
    course this can change, which is much of the reason for the table-driven
    approach used here.
    """

    def __init__(self, pk: PrivateKeyType, key_desc: KeyDesc) -> None:
        self.pk = pk
        self.key_desc = key_desc
        #
        self._jwk: Optional[Dict[str, str]] = None

    ### Key Constructors

    @classmethod
    def create(cls, key_type: str) -> "AcmeKey":
        """
        Factory method to create a new key of key_type, returned as an AcmeKey.
        """

        kdl = [kd for kd in key_table if kd.type_name == key_type]
        if not kdl:
            raise AcmeKeyTypeError("Unknown key_type: %s" % key_type)
        if len(kdl) != 1:
            raise AcmeKeyError(
                "Internal error: key_type %s matches %s entries!" % (key_type, len(kdl))
            )
        kd = kdl[0]

        return cls(kd.generate(kd.gen_arg), kd)

    @classmethod
    def from_pem(cls, pem_data: bytes) -> "AcmeKey":
        """
        load a key from the PEM-format bytes, return an AcmeKey

        NB: since it's not stored in the PEM, the kid is empty (None)
        """

        pk = load_pem_private_key(pem_data, None, default_backend())
        kdl = [kd for kd in key_table if kd.match(pk)]
        if not kdl:
            raise AcmeKeyTypeError("Unknown pk type: %s", type(pk))
        if len(kdl) != 1:
            raise AcmeKeyError(
                "Internal error: key of type %s matches %s entries!" % (type(pk), len(kdl))
            )
        kd = kdl[0]

        return cls(pk, kd)

    @classmethod
    def read_pem(cls, filename: str) -> "AcmeKey":
        "convenience method to load a PEM-format key; returns the AcmeKey"

        with open(filename, "rb") as f:
            return cls.from_pem(f.read())

    ### shared methods

    def to_pem(self) -> bytes:
        "return private key's serialized (PEM) form"

        pem_data = self.pk.private_bytes(
            encoding=Encoding.PEM, format=PrivateFormat.PKCS8, encryption_algorithm=NoEncryption()
        )
        return pem_data

    def write_pem(self, filename: str) -> None:
        "convenience method to write out the key in PEM form"

        with open(filename, "wb") as f:
            f.write(self.to_pem())

    def sign_message(self, message: bytes) -> bytes:
        return self.key_desc.sign(self.pk, message, **self.key_desc.sign_kwargs)


### An ACME account is identified by a key.  When registered there is a Key ID as well.


class AcmeAccount(AcmeKey):
    """
    Only an account key needs (or has) a Key ID associated with it.
    """

    def __init__(self, pk: PrivateKeyType, key_desc: KeyDesc) -> None:
        super().__init__(pk, key_desc)
        self.__kid: Optional[str] = None
        self.__timestamp: Optional[float] = None
        self.__jwk: Optional[Dict[str, str]] = None

    ### kid's descriptor methods

    def get_kid(self) -> str:
        if self.__kid is None:
            raise AcmeKidError("Attempt to access a Key ID that hasn't been set.  Register key?")
        return self.__kid

    def set_kid(self, kid: str, timestamp: float = None) -> None:
        "The kid can be set only once, but we overlook exact duplicate set calls"

        if self.__kid and self.__kid != kid:
            raise AcmeKidError("Cannot alter a key's kid")
        self.__kid = kid
        self.__timestamp = timestamp if timestamp is not None else time.time()

    def del_kid(self) -> None:
        "Doesn't actually del the hidden attribute, just resets the value to None (empty)"
        self.__kid = None

    kid = property(get_kid, set_kid, del_kid)

    def has_kid(self) -> bool:
        "need a non-exploding test for the presence of a Key ID"
        return not self.__kid is None

    ### extend AcmeKey with new methods

    def jwk(self) -> Dict[str, str]:
        """
        Returns the key's JWK as a dictionary

        CACHES result in _jwk
        """

        if not self.__jwk:
            pubnums = self.pk.public_key().public_numbers()
            jwk = dict(self.key_desc.jwk["const"])
            for name, attr_name in self.key_desc.jwk["attrib"].items():
                val = getattr(pubnums, attr_name)
                numbytes = self.key_desc.jwk["nbytes"]
                if numbytes == 0:
                    numbytes = (val.bit_length() + 7) // 8
                jwk[name] = safe_base64(val.to_bytes(numbytes, "big"))
            self.__jwk = jwk
        return self.__jwk

    ### TODO ### store & load file format with kid, timestamp and pk.
    #
    # The PEM RFC says that at least most implementations accept prefixed
    # attributes which would give us something like
    #
    # KID: https://acme-v02.api.letsencrypt.org/acme/account/1a2b3c4d5e6f7g8h9i0j
    # Timestamp: 1600452956.446775
    # -----BEGIN PRIVATE KEY-----
    #
    # Both openssl pkey and the cryptography library can load a PEM decorated
    # like that.  Only possible question is whether the '\n' line ending needs
    # to be adjusted for non-Unix systems.


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
