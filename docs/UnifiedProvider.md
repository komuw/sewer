# DNS and HTTP challenges unified

_There's still a draft when the wind is blowing, but it's getting less._

## Dedication

It is indisputable that this is, in the first instance, Alec Troemel's fault,
since he added support for http-01 challenges.
Also indisputable is that the many changes to both code and overall design
made in the process of unifying the two types of challenges,
while influenced by Alec's code and our discussions, are entirely my fault.
Alec cannot be blamed for my choices!

## A few words about words

Because the word "provider" is so overloaded, I'm going to refer to the
service-specific implementations as "drivers", except when I forget, or
missed changing an old use.  "Provider" is still used in the class names.  And
then there are the "service providers", viz., DNS services or web hosts,
etc.

## Overview (tl;dr)

`ProviderBase` described here defines the interface the ACME engine uses
with new-model drivers (all http-01 drivers, as there are no old ones).  New
drivers normally should inherit from the `DNSProviderBase` or
`HTTPProviderBase` classes in auth.py.

`DNSProviderBase` has support for [aliasing](docs/Aliasing), though the
individual drivers need to be created (or modified) to support it at this
time.  _unbound_ssh is a quirky but working example that supports aliasing.`

## ProviderBase interface for ACME engine

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

## `ProviderBase`

Abstract base class for driver implementations ultimately inherit from.

### ProviderBase __init__

    __init__(self,
        *,
        chal_types: Sequence[str],
        logger: Optional[LoggerType] = None,
        LOG_LEVEL: Optional[str] = "INFO",
        prop_delay: int = 0
        prop_timeout: int = 0,
        prop_sleep_times: Union[Sequence[int], int] = (1, 2, 4, 8)
    ) -> None:


The drivers' `__init__` methods accept only keyword arguments.  We can see
that ProviderBase has become the final recipient of quite a few, mostly
optional, arguments.  They ended up here because they are not specific to a
subclass; a counterexample is the `alias` parameter, which is handled in
`DNSProviderBase`.  The conventions for ProviderBase and its subclasses are:
- keyword only arguments (other than self, of course)
- Required arguments never have a default value
- Optional arguments must have a default, of course
- Everything not explicitly handled is left to kwargs

Conveniently, ProviderBase's __init__ demonstrates all of these aside from
the use of kwargs (because it is the final base class, so any unrecognized
arguments would be in error):
- chal_types is required, so it has no default value and will be diagnosed by
  Python's calling mechanism if omitted.
- logger/LOG_LEVEL are...  weird.  Without the legacy DNS providers I would
  be inclined to just require logger, pushing the job of setting up logging
  firmly back up the stack.  As it is, logger cannot be required (yet), so
  both have defaults that work with the __init__ logic to setup logging as
  sanely as possible.  Eventually LOG_LEVEL should get deprecated and then
  dropped, and logger is just required...
- the prop_* arguments are all optional, and receive default values that the
  engine code is designed to deal with - by disabling the optional behavior
  they control.  These are all parameters that were introduced for a
  lower-level driver or driverBase class, but which have migrated up to
  ProviderBase because they may apply to any sort of Provider.

In all subclasses, kwargs is expected to catch parameters that may need to
pass up the Provider classes, and so it must be passed to super()__init__. 
It is allowed to add, change, or even remove items from kwargs if necessary

--- see the intermediate *ProviderBase classes.

--- (see where for args documentation?  DNS-Alias and DNS-Propagation & ???)

### `setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

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

### `unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

This method is expected to be needed mostly for DNS challenges, but it
should be used whenever a service provider has a relatively slow or
unpredictable lag between the challenge being posted by `setup` and that
challenge data being visible to the world.  When there's no expectation of
such lag, or no way to reliably check that the challenge has propagated,
this may as well just return an empty list, and we'll all hope for the best.

### `clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[Tuple[str, str, Dict[str, str]]]`

`clear`, unlike `setup`, SHOULD NOT stop processing challenges after hitting
an error.  It's possible that any reported errors will be treated as
potential soft errors and the operation retried (with only the unready
challenges).

_? should have a status word for "this one's hard failed, forget about it"?_

## `DNSProviderBase`

The driver *interface* is the same for everything except legacy DNS drivers,
but there are some differences which it makes no sense to push into
`ProviderBase`.  `DNSProviderBase` provides a nice example of this:

`__init__(self, *, alias: str = "", **kwargs: Any) -> None`

def cname_domain(self, chal: Dict[str, str]) -> Union[str, None]

def target_domain(self, chal: Dict[str, str]) -> str

The class's `__init__` handles the `alias` argument, and provides chal_types
suitable for a DNS driver if they weren't already present.  Its value, if
any, is stored locally for use by the helper methods.  `target_domain` is to
be used in the driver to get the actual DNS name for the challenge TXT,
handling both the aliasing and non-aliasing case.  `cname_domain` forms the
DNS name for the CNAME that should exist in the aliasing case and returns it
for the use of a hypothetical sanity check, or None when not aliasing.

## `HTTPProviderBase`

This intermediate base class stands ready to handle any HTTP-specific
options or helper methods.  No additions are expected until sewer has had
some actual drivers added.  It also provides chal_types if needed.
