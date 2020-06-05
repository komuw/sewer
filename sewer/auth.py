from .lib import create_logger
from typing import Any, Dict, Sequence, Tuple, Union

ErrataItemType = Tuple[str, str, Dict[str, str]]


class ProviderBase:
    """
    New-model driver documentation is in docs/UnifiedProvider.md
    """

    def __init__(self, **kwargs: Any) -> None:
        # REQUIRED chal_types - with "fail fast" strict checking
        chal_types = kwargs.pop("chal_types")
        if not isinstance(chal_types, (list, tuple)) or any(
            not isinstance(ct, str) for ct in chal_types
        ):
            raise ValueError("chal_types must be a list or tuple of strings, not: %s" % chal_types)
        self.chal_types = chal_types

        # OPTIONAL logger or LOG_LEVEL (obsolescent) - setup logging; exactly one is accepted!
        if "logger" in kwargs:
            self.logger = kwargs.pop("logger")
        else:
            self.logger = create_logger(__name__, kwargs.pop("LOG_LEVEL", "INFO"))

        # OPTIONAL prop_timeout - how long to wait for unpropagated list to clear?
        self.prop_timeout = kwargs.pop("prop_timeout", 0)

        # OPTIONAL prop_sleep_times - int or sequence of ints of seconds to sleep
        if "prop_sleep_times" not in kwargs:
            self.prop_sleep_times = [1, 2, 4, 8]  # default: sleep for 1, 2, 4, 8, 8 ...
        else:
            pst = kwargs.pop("prop_sleep_times")
            if isinstance(pst, int):
                self.prop_sleep_times = [pst]
            elif isinstance(pst, (list, tuple)):
                if any(not isinstance(value, int) for value in pst):
                    raise ValueError("prop_sleep_times list includes non-int value: %s" % pst)
                self.prop_sleep_times = list(pst)
            else:
                raise ValueError("prop_sleep_time must be Union[int, Sequence[int]]: %s" % pst)

        # UNKNOWN ARGS LEFTOVER?  Could be it got more than one of the logging args.
        if kwargs:
            raise ValueError("BaseAuth was passed unknown or redundant argument(s): %s" % kwargs)

    def setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        raise NotImplementedError("setup method not implemented by %s" % self.__class__)

    def unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        raise NotImplementedError("unpropagated method not implemented by %s" % self.__class__)

    def clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        raise NotImplementedError("clear method not implemented by %s" % self.__class__)


class HTTPProviderBase(ProviderBase):
    """
    Base class for new-model HTTP drivers

    Currently this is a null adapter, holding a place in line for any future shared
    implementation.  It may never become non-null aside from the default chal_types
    it provides, but it's a small price to pay to avoid having to stuff it in later.
    """

    def __init__(self, **kwargs: Any) -> None:
        if "chal_types" not in kwargs:
            kwargs["chal_types"] = ["http-01"]
        super().__init__(**kwargs)


class DNSProviderBase(ProviderBase):
    """
    Base class for new-model DNS drivers - legacy drivers use the one in common.py

    This is a placeholder for now, implementing only the initialization where it
    captures the upcoming alias parameter.  Implementation details for alias are TBD.
    """

    def __init__(self, **kwargs: Any) -> None:
        alias = kwargs.pop("alias", None)
        if "chal_types" not in kwargs:
            kwargs["chal_types"] = ["dns-01"]
        super().__init__(**kwargs)
        self.alias = alias

    ### minimal support for using a DNS alias to hold the challenge response

    def cname_domain(self, chal: Dict[str, str]) -> Union[str, None]:
        return "_acme-challenge." + chal["domain"] if self.alias else None

    def target_domain(self, chal: Dict[str, str]) -> str:
        d = chal["domain"]
        return "_acme-challenge." + d if not self.alias else d + "." + self.alias
