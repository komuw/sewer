# Waiting for the Challenge to Propagate

When you use a service provider's API to setup a challenge response, how
long does it take before the ACME server can reliably get that answer? 
Especially with global anycast DNS services, it can take a while!  This
delay between _posted to API_ and _actually online everywhere that matters_
is the propagation delay we're talking about here.

## How shall we wait, let me count the ways

sewer provides two kinds of delay that can be used to deal with propagation
within the service provider's systems.  Although this was designed mostly
for DNS validation, it may be needed for other types depending on the
service provider.  The two kinds of delay are (1) an unconditional sleep and
(2) an iterative probe/sleep delay loop that has a timeout to keep it from
waiting _too long_.

### To sleep, perchance t'will be enough

The unconditional sleep is implemented in the sewer core logic and is
available to any driver which can pass `prop_delay=seconds_to_sleep` along
to its parent, and so upwards to `ProviderBase`.  If set to a positive
value, it simply sleeps for that number of seconds after the challenges have
all been setup.

--- Available in drivers in 0.8.3.

### Check twice, respond once

The iterative probe is a more active sort of delay: it repeatedly calls the
driver's `unpropagated` method to test whether the challenges are all in
place.  Sadly, the service providers who most need this kind of check are
probably the ones it is most difficult to meaningfully test: by design, you
cannot know which anycast DNS or CDN machine(s) the ACME server will query,
now which ones you'll get in a simple probe by DNS name.  Some service
providers may give you a way to query through their API.  Do what you can...

There are two parameters that manage this: `prop_timeout` and the optional
`prop_sleep_times`.  The first has to be present for the probing to happen
at all; by default this checking is skipped.  the sleep times is an array of
integers, with a default value [1, 2, 4, 8] which causes the loop to sleep 1
second after the first probe if the challenges are not all ready, then 2, 4,
8, and ever after 8 seconds, continuing until it's been at least
prop_timeout seconds since the first probe.

This does also require an implementaion of the `unpropagated` method in the
driver.  The only sane default, used in the legacy drivers' shim class, is
to always return success without any actual checking.

## Advice to driver authors and users

Authors: If the service gives you a way to do a meaningful check and it's
needed, please implement `unpropagated`, and mention that in the driver's
documentation.  Otherwise, just make sure it inherits or implements a null
check.  Feel free to set default values for delay and/or timeout if its
predictable enough, but be sure not to overide the values if the user passes
his own into the driver.  And document, document, document!

Users: Check those driver docs to see what's supported.  Most of the time, a
goodly `prop_delay` will get you past the propagation most of the time, and
is more likely to be available.

_Driver docs are a WIP.  Currently not much to see other than the features
table in [dns-01](dns-01), such as it is._
