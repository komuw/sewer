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

from typing import Any, Callable, cast, Dict, List, Optional, Tuple, Type, Union

from .lib import AcmeError, safe_base64


class AcmeAbstractError(AcmeError):
    pass


### Exceptions specific to ACME crypto operations


class AcmeKeyError(AcmeError):
    pass


class AcmeKeyTypeError(AcmeError):
    pass


class AcmeKidError(AcmeKeyError):
    pass


### types for things defined here

### FIX ME ### is there any way to eliminate the repetition here?  cryptography classes...

private_key_types = (openssl.rsa._RSAPrivateKey, openssl.ec._EllipticCurvePrivateKey)
PrivateKeyType = Union[openssl.rsa._RSAPrivateKey, openssl.ec._EllipticCurvePrivateKey]


### low level key type table


class KeyDesc:

    pk_type: PrivateKeyType

    def __init__(
        self,
        key_size: int,
        type_name: str,
        jwk_const: Dict[str, str],
        jwk_attr: Dict[str, str],
        alg: str,
        key_bytes: int,
    ) -> None:
        self.key_size = key_size
        self.type_name = type_name
        self.jwk_const = jwk_const
        self.jwk_attr = jwk_attr
        self.alg = alg
        self.key_bytes = key_bytes

    def generate(self) -> PrivateKeyType:
        raise AcmeAbstractError("KeyDesc.generate")

    def sign(self, pk: PrivateKeyType, message: bytes) -> bytes:
        raise AcmeAbstractError("KeyDesc.sign")

    def match(self, pk: PrivateKeyType) -> bool:
        if isinstance(pk, self.pk_type) and pk.key_size == self.key_size:
            return True
        return False


class RsaKeyDesc(KeyDesc):

    pk_type = rsa.RSAPrivateKey

    def __init__(self, key_size: int) -> None:
        type_name = "rsa%s" % key_size
        super().__init__(key_size, type_name, {"kty": "RSA"}, {"e": "e", "n": "n"}, "RS256", 0)

    def generate(self) -> PrivateKeyType:
        return rsa.generate_private_key(65537, self.key_size, default_backend())

    def sign(self, pk: PrivateKeyType, message: bytes) -> bytes:
        "Yes, SHA256 is hardwired.  As of Sep 2020, LE rejects other hashes for RSA"

        return pk.sign(message, padding.PKCS1v15(), hashes.SHA256())


class EcKeyDesc(KeyDesc):

    pk_type = ec.EllipticCurvePrivateKey

    def __init__(self, key_size: int, hash_type, alg: str, key_bytes: int) -> None:
        name = "secp%sr1" % key_size
        curve = "P-%s" % key_size
        super().__init__(
            key_size, name, {"kty": "EC", "crv": curve}, {"x": "x", "y": "y"}, alg, key_bytes
        )
        self.curve = getattr(ec, name.upper())
        self.hash_type = hash_type

    def generate(self) -> PrivateKeyType:
        return ec.generate_private_key(self.curve, default_backend())

    def sign(self, pk: PrivateKeyType, message: bytes) -> bytes:
        # EC sign method returns ASN.1 encoded values for some inane reason
        r, s = utils.decode_dss_signature(pk.sign(message, ec.ECDSA(self.hash_type())))
        return r.to_bytes(self.key_bytes, "big") + s.to_bytes(self.key_bytes, "big")


key_table = [
    RsaKeyDesc(2048),
    RsaKeyDesc(3072),
    RsaKeyDesc(4096),
    EcKeyDesc(256, hashes.SHA256, "ES256", 32),
    EcKeyDesc(384, hashes.SHA384, "ES384", 48),
    # EcKeyDesc(521, hashes.SHA512, 64, "ES512", 66),  this is where the key size != hash size?
]

# extract just the names for option choice lists, etc.
key_type_choices = [kd.type_name for kd in key_table]


def resolve_key_desc(key: Union[str, PrivateKeyType]) -> KeyDesc:
    """
    Given a private key or a registered key type name, find the unique matching
    descriptor and return it.

    Raises exceptions if no match is found or if more than one matches (internal
    table error!).
    """

    if isinstance(key, private_key_types):
        kdl = [kd for kd in key_table if kd.match(key)]
        kt = str(type(key))
    else:
        kdl = [kd for kd in key_table if kd.type_name == key]
        kt = key
    if not kdl:
        raise AcmeKeyTypeError("Unknown key type: %s", kt)
    if len(kdl) != 1:
        raise AcmeKeyError("Internal error: key type %s matches %s entries!" % (kt, len(kdl)))
    return kdl[0]


### AcmeKey, finally!


AcmeKeyType = Union["AcmeKey", "AcmeAccount"]


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
    def create(cls: Type["AcmeKey"], key_type_name: str) -> "AcmeKey":
        """
        Factory method to create a new key of key_type, returned as an AcmeKey.
        """

        kd = resolve_key_desc(key_type_name)
        return cls(kd.generate(), kd)

    @classmethod
    def from_pem(cls: Type["AcmeKey"], pem_data: bytes) -> "AcmeKey":
        """
        load a key from the PEM-format bytes, return an AcmeKey

        NB: since it's not stored in the PEM, the kid is empty (None)
        """

        pk = load_pem_private_key(pem_data, None, default_backend())
        kd = resolve_key_desc(pk)

        return cls(pk, kd)

    @classmethod
    def read_pem(cls: Type["AcmeKey"], filename: str) -> "AcmeKey":
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
        return self.key_desc.sign(self.pk, message)


### An ACME account is identified by a key.  When registered there is a Key ID as well.


class AcmeAccount(AcmeKey):
    """
    Only an account key needs (or has) a Key ID associated with it.
    """

    def __init__(self, pk: PrivateKeyType, key_desc: KeyDesc = None) -> None:
        if key_desc is None:
            key_desc = resolve_key_desc(pk)
        super().__init__(pk, key_desc)
        self.__kid: Optional[str] = None
        self._timestamp: Optional[float] = None
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
        self._timestamp = timestamp if timestamp is not None else time.time()

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
            jwk = {}
            pubnums = self.pk.public_key().public_numbers()
            jwk.update(self.key_desc.jwk_const)
            for name, attr_name in self.key_desc.jwk_attr.items():
                val = getattr(pubnums, attr_name)
                numbytes = self.key_desc.key_bytes
                if numbytes == 0:
                    numbytes = (val.bit_length() + 7) // 8
                jwk[name] = safe_base64(val.to_bytes(numbytes, "big"))
            self.__jwk = jwk
        return self.__jwk

    ### TODO ### store & load file format with kid, timestamp and pk.
    #
    # RFC7568 says that at least most implementations accept text outside the
    # BEGIN...END lines, especially in PKIX certificates.  So I plan to do
    # something like this:
    #
    # KID: https://acme-v02.api.letsencrypt.org/acme/account/1a2b3c4d5e6f7g8h9i0j
    # Timestamp: 1600452956.446775
    # -----BEGIN PRIVATE KEY-----
    #
    # Both openssl pkey and the cryptography library can load a PEM decorated
    # like that.  Only possible question is whether the '\n' line ending needs
    # to be adjusted for non-Unix systems.

    def write_key(self, filename: str) -> None:
        "Like write_pem but prepends the KID and timestamp if those are present"

        with open(filename, "wb") as f:
            if self.__kid:
                f.write(("KID: %s\n" % self.__kid).encode())
                if self._timestamp:
                    f.write(("Timestamp: %s\n" % self._timestamp).encode())
            f.write(self.to_pem())

    @classmethod
    def read_key(cls: Type["AcmeAccount"], filename: str) -> "AcmeAccount":
        with open(filename, "rb") as f:
            data = f.read()
        prefix = b""
        n = data.find(b"-----BEGIN")
        if 0 < n:
            prefix = data[:n]
            data = data[n:]
        acct = cast("AcmeAccount", cls.from_pem(data))
        if prefix:
            parts = prefix.split(b"\n")
            for p in parts:
                if p.startswith(b"KID: "):
                    acct.__kid = p[5:].decode()
                elif p.startswith(b"Timestamp: "):
                    acct._timestamp = float(p[11:])
        return acct


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
