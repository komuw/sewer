#### `unpropagated` method and intelligent waiting

The `unpropagated` method provides a hook where the driver MAY check that
the challenge responses that were configured by `setup` are actually
accessible to the ACME server.  This is, of necessity, no more than a
best-effort check, but since LE only attempts to validate a challenge once,
then marks it invalid if it didn't succeed, it will sometimes be worth
doing.

There are two parameters that are set through the driver's __init__ and used
by the ACME engine to manage this checking.  The first is `prop_timeout`,
which must be set to a positive value for `unpropagated` to be called at all. 
When set, it is the overall timeout in seconds.  This might be set by the
driver for services that are known to take a while, but if so that value
SHOULD be overridden by an explicit keyword argument.

The second parameter is probably less often needed, and has a default that
ought to be reasonable in most cases.  `prop_sleep_times` is a list of
seconds to sleep after a failed call to `unpropagated`.  The values are used
in order, so the default [1, 2, 4, 8] sleeps for 1 second, then 2 seconds,
then 4 seconds, then 8 seconds every subsequent time.  There's one special
case: `prop_sleep_times` may be a single integer, which sleeps for that
fixed delay following every failed check.

The timeout is not quite a hard one: it is checked immediately after a
failed call to `unpropagated`, and if it has not been exceeded there will be
a sleep of whatever time followed by another check.  The loop keeps checking
for AT LEAST `prop_timeout` seconds.

Mentioned for completeness: if a driver wishes to just add a fixed delay
between `setup` and signalling the ACME server to validate the challenges,
it could implement `unpropagated` as just sleep(delay) and return success (an
empty errata list).  NB: it still needs a non-zero `prop_timeout` for the
driver to pass up to `super().__init__`.
