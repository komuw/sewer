import base64, codecs, json, logging, os
from hashlib import sha256
from typing import Any, Union

LoggerType = logging.Logger


class SewerError(Exception):
    "base class for sewer-related exceptions"
    pass


class AcmeError(SewerError):
    "base class [and, inevitably, catch-all] for ACME related errors"
    pass


class AcmeRegistrationError(AcmeError):
    pass


### FIX ME ### can be more specific about response arg's type... somehow


def log_response(response: Any) -> str:
    """
    renders a python-requests response as json or as a string
    """
    try:
        log_body = response.json()
    except ValueError:
        log_body = response.content[:40]
    return log_body


def create_logger(name: str, log_level: Union[str, int]) -> LoggerType:
    """
    return a logger configured with name and log_level
    """

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def safe_base64(un_encoded_data: Union[str, bytes]) -> str:
    "return ACME-safe base64 encoding of un_encoded_data as a string"

    if isinstance(un_encoded_data, str):
        un_encoded_data = un_encoded_data.encode("utf8")
    r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
    return r.decode("utf8")


def dns_challenge(key_auth: str) -> str:
    "return the ACME challenge response for a DNS TXT record"

    return safe_base64(sha256(key_auth.encode("utf8")).digest())


_sewer_meta = None


def sewer_meta(name: str) -> str:
    """
    returns the named attribute from lazily-loaded  meta.json (replaces __version__.py)
    """

    global _sewer_meta

    if _sewer_meta is None:
        here = os.path.abspath(os.path.dirname(__file__))
        with codecs.open(os.path.join(here, "meta.json"), "r", encoding="utf8") as f:
            _sewer_meta = json.load(f)
    return _sewer_meta[name]
