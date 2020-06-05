## DNS and HTTP challenges unified

*DRAFT VERSION*  May 31st 2020 - prop_delay added.  Was: file name changed; stub challenge-specific
bases added.

It is indisputable that this is, in the first instance, Alec Troemel's fault,
since he added support for http-01 challenges.
Also indisputable is that the many changes to both code and overall design
made in the process of unifying the two types of challenges,
while influenced by Alec's code and our discussions,
are entirely my fault.
Alec cannot be blamed for my choices!

_Because the word "provider" is so overloaded, I'm going to refer to the
service-specific implementations as "drivers", except when I forget, or
overlooked an old usage.  "Provider" is still used in the class names.  And
then there are the "service providers", viz., DNS services or web hosts,
etc._

`ProviderBase` described here defines the interface the ACME engine uses
with new-model drivers (all http-01 drivers, as there are no old ones).  New
drivers should inherit from the `DNSProviderBase` or `HTTPProviderBase`
classes in auth.py.  At this time the only functioanlity these add is
setting up the `chal_types` parameter, and for DNS collecting the not yet
implemented `alias` parameter.

> For the alias feature, there are several moving parts, some optional.
I would like to support checking that the CNAMEs are provisioned.
Currently that requires adding a dependency (probably dnspython?),
but that may be necessary anyway for implementing unpropagated.
The ~~engine~~ `DNSProviderBase` class can compose the names for the CNAME
record as well as the alias record, and if doing the full checking it may need
to do so, so I ~~am considering~~ have added `DNSProviderBase` with an
optional `alias` parameter and simple methods to turn a challenge's domain
into the fqdn of the CNAME (if there is one) and the target where the
challenge response will be placed.  Brand new and subject to change...

> Also just added `HTTPProviderBase` which hasn't acquired any interesting
features yet, and may never do so, but it seems a tiny cost to prevent the
disruption its absence could result in at some later date.

All the existing DNS drivers were written to the legacy interface, and are
supported through a shim class in dns_providers.common, `BaseDns`.  These
legacy implementations will, hopefully, be migrated to the new-model
interface.  The assistance of the authors and/or current users of each
driver will be needed!

### ProviderBase interface for ACME engine

The interface between the ACME protocol code and any driver implementation
consists of three methods, `setup`, `unpropagated` and `clear`.  The first
and last are not unlike methods used by the legacy drivers, but they accept
a list of one or more challenges rather than one challenge at a time.

The `unpropagated` method was added with DNS propagation delays in mind.  It
should be possible for legacy drivers to implement this without a full
conversion to the new-model as a temporary adaptation for those who need
this feature.  Just override the null version provided by `BaseDns`. 

`unpropagated` checks all the challenges in the list it is passed, and
returns a list containing the ones which are *not* yet ready to be
validated.  This should be more reliable than adding an ad-hoc delay before
_responding_ to the ACME server as well as avoiding wasting time.

The errata list returned by by all three methods has tuples for elements,
where each tuple holds three values: the status, the msg, and the original,
unmodified challenge item (dictionary).  _Recent change, may not have fixed
all other ideas in code or docs yet._

> LE's ACME server, for one, implements neither automatic nor
triggered retries, so it's important not to _respond_ to a challenge before
the validation response is actually accessible.  And yes, the RFC's language
does encourage confusing the respond-to-challenge API request with the
validation response that the server has to get when it probes for it.

> My thinking on this is that, while the ACME engine's code can know what
names to check, in the really interesting case of widely distributed
(anycast?) DNS service, figuring out which DNS server to query must be left
to the service-specific driver.  In some cases the service may provide an
API for checking some internal status that might be faster and/or more
reliable than polling DNS servers.  For cases where all that can (or needs)
to be done is some DNS lookups, well, that can be packaged as a function.

This is the pattern which all three methods use: accept a list of challenges
(each a dictionary) to process, and return an errata list containing the
subset which have problems or are not ready.  So in all cases an empty list
returned means that all went well.

### `ProviderBase`

Abstract base class for driver implementations to inherit from.  There is
also a child class, `BaseDns` that the legacy drivers are based on which
shims their old DNS-only interface.

#### `__init__(self, **kwargs: Any) -> None`

All native driver classes take only `**kwargs` parameters.  Derived classes
MUST extract the parameters they recognize and process them, which includes
raising an exception for missing required values, etc.  They MUST ignore
names they don't recognize and pass them along to `super()__init__`.  They
MAY add or modify parameters before passing the parameters to their
parent's` __init__`.

`ProviderBase` differs only in that unrecognized parameters, viz., any that
are left after its own known parameters are extracted, are reported as an
error.  The parameters which `ProviderBase` will recognize are:

| name |status | value type | description |
| --- | --- | --- | --- |
| chal_types | REQUIRED | `Sequence[str]` | The ACME challenge types the child class can satisfy. |
| logger | REQ 1 of 2 | `str` | A configured logging object to use by the driver |
| LOG_LEVEL | REQ 2 of 2 | `Union[str, int]` | Old way to setup logging. Only one of logger and LOG_LEVEL can be used |
| prop_delay | OPTIONAL | int | If passed, then wait up to this long for unpropagated eratta list to clear.  Default is no delay. |

> This morning's ah-ha moment was in two closely spaced parts.  Imprimis,
that the wait time for propagation OUGHT to come from the driver, since
that's where [DNS or other] service-specific info belongs.  Oh, and
prop_delay is a good name for the driver attribute.  And default is None ->
no delay -> no call to check.  Secundus, that this SHOULD be collected all
the way at the top, in `ProviderBase` to insure there is always a prop_delay
attribute because that delay is now an internal protocol parameter.  And
even though I can't see why, now, it could be needed for other challenge
types.

#### `setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

The `setup` method is called to publish one or more challenges.  Each item
in the list describes one challenge.

(_the description of the challenges list is common to all three methods_)

The items are dictionaries with keys and values that come from the ACME
authz query, or are derived from it and the account key [see note].
For dns-01 and http-01 challenges, the required keys are:

* ident_value - the value of the identifier to be validated (1)
* token - the validation nonce
* key_auth - validation value (hash of nonce + secret key's thumbprint)

> The current per-challenge dict holds a subset of the authz values, and
some of the names (and structure) are different.  *This is likely to change
in the future!* (0.9?)

The plan is to include other values from the ACME _authorization object_
response, as well as non-authz values, so the driver implementation MUST
accept additional keys in the dictionary.  Likewise, the list SHOULD include
only outstanding challenges, and the call(s) to the driver SHOULD be omitted
if there are none.  But the latter, especially, is just the plan, so
throwing an exception if the challenges list is empty is JUST NOT ON.

> Allowing an empty challenges list is also convenient for unit tests.

Each of the three methods return an errata list of the challenge items which
encountered an issue - couldn't create, isn't published, removal failed.  So
in all cases, an empty list means all is well.

The *errata list* is a list-like containing a tuple for each failed or
unready challenge.  The tuples have three elements: a status (str), a msg
(str) intended to enlighten a human observer, and the original challenge
item (the dictionary from the argument list).  The status MUST be one of the
defined values:

| status | applies to | meaning |
| --- | --- | --- |
| "failed" | all | challenge for which a failure occurred |
| "skipped" | setup | may skip challenges after one has a hard failure |
| "unready" | unpropagated | soft fail: record not deployed to authoritative server(s).  If a non-recoverable error is detected, then use _failed_. |

#### `unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

This method is expected to be needed mostly for DNS challenges, but it
should be used whenever a service provider has a relatively slow or
unpredictable lag between the challenge being posted by `setup` and that
challenge data being visible to the world.  When there's no expectation of
such lag, or no way to reliably check that the challenge has propagated,
this may as well just return an empty list, and we'll all hope for the best.

#### `clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

`clear`, unlike `setup`, SHOULD NOT stop processing challenges after hitting
an error.  It's possible that any reported errors will be treated as
potential soft errors and the operation retried (with only the unready
challenges).

_? should have a status word for "this one's hard failed, forget about it"?_

### `DNSProviderBase`

Accepts the `alias` parameter and provides chal_types if not passed in. 
Defines two methods that use the `alias` string (or its absence, the default
condition) and a challenge dict to form the target_domain name (where the
TXT with the challenge response data goes) and, if `alias` was specified, the
cname_domain where the CNAME should be.

> This could allow a hypothetical library function to attempt to verify the
propagation, and that might happen in the future.  It doesn't really address
the problems of a really widespread (anycast, other names?) service provider
where there may be no way to enumerate "the authoritative nameservers".

NB: `self.target_domain(chal)` SHOULD be used to form the DNS name for the
TXT record unless you're doing something very strange.

### `HTTPProviderBase`

Does nothing aside from setting up chal_types as `["http-01"]` if it's not
already there.  They also serve who only redirect...
