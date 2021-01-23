## Legacy DNS challenge providers

### `BaseDns` shim class

A child of `DNSProviderBase` that acts as an adapter between the new
Provider interface and the legacy DNS provider interface.

#### `__init__(self, **kwargs: Any) -> None`

Accepts no arguments itself; doesn't expect any to be passed by Legacy code.
Injects `chal_types=["dns-01"]`.

#### `setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Iterates over the challenges, extracting the values needed for the legacy
DNS interface from each challenge in the list, and passing them to
`create_dns_record`.  Always returns an empty list since there is no error
return from `create_dns_record` other than raising an exception.

#### `unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Always returns an empty list, signalling "all ready as far as I know".
A legacy DNS driver wishing to do something useful here MAY implement
`unpropagated` without updating the rest of its interface.

#### `clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Dict[str, str]]`

Same as setup except it calls the legacy `delete_dns_record`, of course.

### Legacy DNS class

#### `__init__(self, ..., **kwargs)`

Args handled by the driver should be explicitly named, with defaults where
that makes sense.  Starting in 0.8.3, the `**kwargs` bucket has been added
to provide pass-through to the base class.

#### `def create_dns_record(self, domain_name, domain_dns_value)`

Minimum is to add `_acme-challenge` prefix to domain_name and post the
challenge response (domain_dns_value) as that name's TXT value.
All very provider-dependent.

#### `def delete_dns_record(self, domain_name, domain_dns_value)`

In theory it should undo the effects of setup.
In practice, at least one of the services is unable to do that
(according to the author's comment).

### Legacy DNS vs Aliasing

Legacy DNS drivers MAY change to use the [aliasing](ALiasing) methods
inherited from `DNSProviderBase`, though this will require a potentially
fragile faking of the new-model challenge dict in the driver.  See the
`unbound_ssh` example driver, and bear in mind that a change to the data
type of the challenge items IS anticipated, perhaps in 0.9.
