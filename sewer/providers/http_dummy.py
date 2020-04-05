"Dummy http-01 provider for testing"

from typing import List, Sequence, Tuple

from ..auth import BaseAuth


class BaseHttpDummy(BaseAuth):
    def __init__(self, **kwargs):
        kwargs.setdefault("chal_types", ["http-01"])
        super(BaseHttpDummy, self).__init__(**kwargs)
        self.active_challenges = []

    def check_and_clear(self) -> List[Tuple[str, str, str]]:
        leftovers = self.active_challenges
        self.active_challenges = []
        return leftovers


class HttpDummyCert(BaseHttpDummy):
    "HTTP testing dummy that implements *_cert methods"

    def setup_cert(self, authorizations: Sequence[Tuple[str, str, str]]) -> None:
        self.active_challenges.extend(authorizations)

    def is_ready_cert(self, authorizations: Sequence[Tuple[str, str, str]]) -> bool:
        return all(auth in self.active_challenges for auth in authorizations)

    def clear_cert(self, authorizations: Sequence[Tuple[str, str, str]]) -> None:
        for auth in authorizations:
            self.active_challenges.remove(auth)


class HttpDummyAuth(BaseHttpDummy):
    "HTTP testing dummy that implements *_auth methods"

    def setup_auth(self, domain: str, token: str, key_auth: str) -> None:
        self.active_challenges.append((domain, token, key_auth))

    def is_ready_auth(self, domain: str, token: str, key_auth: str) -> bool:
        return (domain, token, key_auth) in self.active_challenges

    def clear_auth(self, domain: str, token: str, key_auth: str) -> None:
        self.active_challenges.remove((domain, token, key_auth))
