"demo.py - examples of implementing non-or-minimally-functional challenge providers"

###
### NB: very early draft, minimal testing so far (May 25th)
###

from typing import Any, Dict, Sequence

from ..auth import ProviderBase
from ..dns_providers.common import dns_challenge


class ManualProvider(ProviderBase):
    def __init__(self, **kwargs: Any) -> None:
        chal_type = kwargs.pop("chal_type", "http-01")
        if chal_type not in ["dns-01", "http-01"]:
            raise ValueError("ManualProvider: invalid chal_type value: %s", chal_type)
        kwargs["chal_types"] = [chal_type]
        super().__init__(**kwargs)
        self.chal_type = chal_type

    def setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]:
        return self._prompt("add", challenges)

    def unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]:
        # could add confirmation here, but it's just a demo
        return []

    def clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]:
        return self._prompt("clear", challenges)

    def _prompt(self, mode: str, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]:
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
        return []
