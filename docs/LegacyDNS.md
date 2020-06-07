## Legacy DNS challenge providers

### `BaseDns` shim class

A child of `DNSProviderBase` that acts as an adapter between the Provider
interface and the Legacy DNS provider interface.

#### `__init__(self, **kwargs: Any) -> None`

Accepts no arguments itself; doesn't expect any to be passed by Legacy code.
Injects chal_types=["dns-01"].

#### `setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Iterates over the challenges, extracting the values needed for the Legacy
DNS interface from each challenge in the list, and passing them to
`create_dns_record`.  Always returns an empty list since there is no error
return from `create_dns_record` other than raising an exception.

#### `unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Always returns an empty list, signalling "all ready as far as I know".
A Legacy DNS provider wishing to do something useful here MAY implement
`unpropagated` without migrating the rest of its interface.

#### `clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Same as setup except it calls the legacy `delete_dns_record`, of course.

### Legacy DNS class

#### `__init__(self, ...)`

Args are explicitly named per provider; no provision for passing any to
`super().__init__` - which makes sense, since there used not to be any the
parent (original `BaseDns`) was prepared to receive.

#### `def create_dns_record(self, domain_name, domain_dns_value)`

Minimum is to add `_acme-challenge` prefix to domain_name and post the
challenge response (domain_dns_value) as that name's TXT value.
All very provider-dependent.

#### `def delete_dns_record(self, domain_name, domain_dns_value)`

In theory it should undo the effects of setup.
In practice, at least one of the services is unable to do that
(according to the author's comment).

### Legacy DNS vs Aliasing

Legacy DNS providers MAY adapt to using the [aliasing](DNS-ALiasing), though
a potentially fragile faking of the new-model challenge dict is required. 
See the `unbound_ssh` example driver, and bear in mind that a change to the
data type of the challenge items IS anticipated, perhaps in 0.9.
