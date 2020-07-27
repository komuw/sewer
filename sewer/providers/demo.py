"demo.py - examples of implementing non-or-minimally-functional challenge providers"

# still minimally functional - too handy for testing to make it wait for input

from typing import Any

from ..auth import ChalListType, ErrataListType, ProviderBase
from ..lib import dns_challenge


class ManualProvider(ProviderBase):
    def __init__(self, *, chal_type: str = "http-01", **kwargs: Any) -> None:

        ### FIX ME ### poor example ignores possible chal_types in kwargs?

        # this is unusual: it can accept either DNS or HTTP challenges.  Some sanity checks...
        if chal_type not in ["dns-01", "http-01"]:
            raise ValueError("ManualProvider: invalid chal_type value: %s", chal_type)
        kwargs["chal_types"] = [chal_type]
        super().__init__(**kwargs)
        self.chal_type = chal_type

    def setup(self, challenges: ChalListType) -> ErrataListType:
        return self._prompt("add", challenges)

    def unpropagated(self, challenges: ChalListType) -> ErrataListType:
        # could add confirmation here, but it's just a demo
        return []

    def clear(self, challenges: ChalListType) -> ErrataListType:
        return self._prompt("clear", challenges)

    def _prompt(self, mode: str, challenges: ChalListType) -> ErrataListType:
        for chal in challenges:
            if self.chal_type == "dns-01":
                print(
                    "Please {0} the challenge {1} as a TXT record on _acme-validation.{ident_value}".format(
                        mode, dns_challenge(chal["key_auth"]), **chal
                    )
                )
            else:
                print(
                    "Please {0} the challenge file named {token} with contents {key_auth}".format(
                        mode, **chal
                    )
                )

        ### FIX ME ### using this for some tests, so no prompt "press return when setup"

        return []
