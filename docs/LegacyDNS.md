## Legacy DNS challenge providers

### `BaseDns` shim class

A child of `ProviderBase` that acts as an adapter between the Provider
interface and the Legacy DNS providers.

#### `__init__(self, **kwargs: Any) -> None`

Accepts no arguments itself; doesn't expect any to be passed by Legacy code.
Injects chal_types=["dns-01"].

#### `setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Iterates over the challenges, extracting the values needed for dns-01 from
each challenge in the list, and passing them to create_dns_record.
Always returns an empty list since there is no error return from
create_dns_record other than raising an exception.

#### `unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Always returns an empty list, signalling "all ready as far as I know".
A DNS provider wishing to do something useful here must migrate to the new
API.

#### `clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Same as setup except it calls the legacy delete_dns_record, of course.

### Legacy DNS class

#### `__init__(self, ...)`

Args are explicitly named per provider; no provision for passing any to
`super().__init__` - which makes sense, since there used not to be any the
parent was prepared to receive.

#### `def create_dns_record(self, domain_name, domain_dns_value)`

Minimum is to add `_acme-challenge` prefix to domain_name and post the
challenge response (domain_dns_value) as that name's TXT value.
All very provider-dependent.

#### `def delete_dns_record(self, domain_name, domain_dns_value)`

In theory it should undo the effects of setup.
In practice, at least one of the services is unable to do that
(according to the comment).
