from typing import Any, Dict, Optional, Sequence, Tuple, Union, cast

from .lib import create_logger, LoggerType

ChalItemType = Dict[str, str]
ChalListType = Sequence[ChalItemType]
ErrataItemType = Tuple[str, str, ChalItemType]
ErrataListType = Sequence[ErrataItemType]


class ProviderBase:
    """
    New-model driver documentation is in docs/UnifiedProvider.md
    """

    def __init__(
        self,
        *,
        chal_types: Sequence[str],
        logger: Optional[LoggerType] = None,
        LOG_LEVEL: str = "INFO",
        prop_delay: int = 0,
        prop_timeout: int = 0,
        prop_sleep_times: Union[Sequence[int], int] = (1, 2, 4, 8),
    ) -> None:

        # TypeError if missing, still check that it's a sequencey value; non-str vals, meh
        if not isinstance(chal_types, (list, tuple)):
            raise ValueError("chal_types must be a list or tuple of strings, not: %s" % chal_types)
        self.chal_types = chal_types

        # setup logging.  let it pass if both are given; logger supersedes old LOG_LEVEL
        if logger:
            self.logger = logger
        else:
            self.logger = create_logger(__name__, LOG_LEVEL)

        # prop_* control delay before and timeout of checking loop as well as internal sleeps
        self.prop_delay = int(prop_delay)
        self.prop_timeout = int(prop_timeout)

        ### eratta ### accepts str value(s) that pass int(); low importance
        if isinstance(prop_sleep_times, (list, tuple)):
            self.prop_sleep_times = tuple(int(v) for v in prop_sleep_times)
        else:
            self.prop_sleep_times = (int(cast(int, prop_sleep_times)),)

    def setup(self, challenges: ChalListType) -> ErrataListType:
        raise NotImplementedError("setup method not implemented by %s" % self.__class__)

    def unpropagated(self, challenges: ChalListType) -> ErrataListType:
        raise NotImplementedError("unpropagated method not implemented by %s" % self.__class__)

    def clear(self, challenges: ChalListType) -> ErrataListType:
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

    Accepts the alias optional argument and adds cname_domain and target_domain
    to support the implementation of aliasing in drivers that inherit from it.
    """

    def __init__(self, *, alias: str = "", **kwargs: Any) -> None:
        if "chal_types" not in kwargs:
            kwargs["chal_types"] = ["dns-01"]
        super().__init__(**kwargs)
        self.alias = alias

    ### support for using a DNS alias

    def cname_domain(self, chal: Dict[str, str]) -> Union[str, None]:
        "returns fqdn where CNAME should be if aliasing, else None"

        return "_acme-challenge." + chal["ident_value"] if self.alias else None

    def target_domain(self, chal: Dict[str, str]) -> str:
        "returns fqdn where challenge TXT should be placed"

        d = chal["ident_value"]
        return "_acme-challenge." + d if not self.alias else d + "." + self.alias
