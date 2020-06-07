## DNS and HTTP challenges unified

*DRAFT VERSION*  Jun 16th 2020 - reference DNS-Propagation, Was: prop_delay added.

### Dedication

It is indisputable that this is, in the first instance, Alec Troemel's fault,
since he added support for http-01 challenges.
Also indisputable is that the many changes to both code and overall design
made in the process of unifying the two types of challenges,
while influenced by Alec's code and our discussions,
are entirely my fault.
Alec cannot be blamed for my choices!

### A few words about words

Because the word "provider" is so overloaded, I'm going to refer to the
service-specific implementations as "drivers", except when I forget, or
missed changing an old use.  "Provider" is still used in the class names.  And
then there are the "service providers", viz., DNS services or web hosts,
etc.

### Overview (tl;dr)

`ProviderBase` described here defines the interface the ACME engine uses
with new-model drivers (all http-01 drivers, as there are no old ones).  New
drivers normally should inherit from the `DNSProviderBase` or
`HTTPProviderBase` classes in auth.py.  _(for those who watched the
unification, no, this isn't really dividing them back up - they still have
the identical interface defined in `ProviderBase`.  But there are
unavoidable implementation differences, and once `DNSProviderBase` was added
to anchor the aliasing suport, it just seemed prudent to put
`HTTPProviderBase` there as a hedge against future need.)_

sewer has support for [aliasing](docs/Aliasing), though drivers need to
be created (or modified) to support it at this time.

### ProviderBase interface for ACME engine

The interface between the ACME protocol code and any driver implementation
consists of three methods, `setup`, `unpropagated` and `clear`.  The first
and last are not unlike methods used by the legacy drivers, but they accept
a list of one or more challenges rather than one challenge at a time.

--- most of this is in [unpropagated], or should be.  ToDo: reconcile

The `unpropagated` method was added with DNS propagation delays in mind.  It
should be possible for legacy drivers to implement this without a full
conversion to the new-model as a temporary adaptation for those who need
this feature.  Just override the null version provided by `BaseDns`. 

`unpropagated` checks all the challenges in the list it is passed, and
returns a list containing the ones which are *not* yet ready to be
validated.  This should be more reliable than adding an ad-hoc delay before
_responding_ to the ACME server as well as avoiding wasting time.

The errata list returned by by all three methods has tuples for elements,
where each tuple holds three values: the status string, the msg string, and
the original, unmodified challenge item (dictionary).  This is defined as
types `ErrataItemType` and `ErrataListType` in auth.py

> LE's ACME server, for one, implements neither automatic nor triggered
retries, so it's important not to _respond_ to a challenge before the
validation response is actually accessible.  And yes, the RFC's language
does encourage confusing the respond-to-challenge API request with the
challenge response (TXT) that the server has to find when it probes for it.

> My thinking on this is that, while the ACME engine's code can know what
names to check, in the really interesting case of widely distributed
(anycast?) DNS service, figuring out which DNS server to query must be left
to the service-specific driver.  In some cases the service may provide an
API for checking some internal status that might be faster and/or more
reliable than polling DNS servers.  For cases where all that can (or needs)
to be done is some DNS lookups, well, that can be packaged as a function.

--- end reconcile block

This is the pattern which all three methods use: accept a list of challenges
(each a dictionary) to process, and return an errata list containing the
subset which have problems or are not ready.  So in all cases an empty list
returned means that all went well.

### `ProviderBase`

Abstract base class for driver implementations ultimately inherit from.

#### ProviderBase __init__

    __init__(self,
        *,
        chal_types: Sequence[str],
        logger: Optional[LoggerType] = None,
        LOG_LEVEL: Optional[str] = "INFO",
        alias: Optional[str] = None,
        prop_delay: int = 0
        prop_timeout: int = 0,
        prop_sleep_times: Union[Sequence[int], int] = (1, 2, 4, 8)
    ) -> None:


The drivers' `__init__` methods accept only keyword arguments.  Here we see
that ProviderBase has become the final recipient of quite a few, mostly
optional, arguments.  This is the general form that Provider subclasses are
expected to follow: explicitly list the arguments which that driver requires
after the *, so they must be passed as keyword args, but give no default
value so that they will be diagnosed as missing by the call protocol.

Conveniently, ProviderBase's __init__ has instance of all the variations.
chal_types is required, so it has no default value and will be diagnosed by
Python itself.  logger/LOG_LEVEL are... weird.  Without the legacy DNS
providers I would be inclined to just require logger, pushing the job of
setting up logging firmly back up the stack.  As it is, logger cannot be
required (yet), so both have defaults that work with the __init__ logic to
setup logging as sanely as possible.  Eventually LOG_LEVEL should get
deprecated and then dropped, and logger is just required...

alias and the prop_* arguments are all optional, and have default values
that the engine code is designed to deal with - by disabling the optional
behavior they control.  These are all parameters that were introduced for a
lower-level driver or driverBase class, but which have migrated up to
ProviderBase because they may apply to any sort of Provider.

In all child classes, kwargs is expected to catch parameters that may need
to pass up the Provider classes, and so it must be passed to
super()__init__.  It is allowed to add, change, or even remove items from
kwargs if necessary - see the intermediate *ProviderBase classes.

--- (see where for args documentation?  DNS-Alias and DNS-Propagation & ???)

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
