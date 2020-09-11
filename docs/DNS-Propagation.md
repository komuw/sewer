# Waiting for Mr. DNS or Someone Like Him

Q: How long does it take after you've setup the challenge response TXT records
until they're actually accessible to the ACME server?

A: Good Question!

According to [Let's Encrypt](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
it can take up to an hour.  Depends on the DNS service.  Some provide a way
to check that your changes are fully propagated to all their servers.  With
many, however, you just have to wait.  But be sure you wait long enough,
because Let's Encrypt DOES NOT implement automatic or triggered retry of a
failed authorization - you have to restart the [same] order or else start
all over again.

Sewer provides a flexible _delay until actually published_ mechanism through
three optional driver parameters, `prop_delay`, `prop_timeout`,
`prop_sleep_times`, and the [`unpropagated` method](unpropagated).
Let's see how they're used in various circumstances.

## No API support, no reliable way to check: just delay

If you can't check that the TXT records are fully published, then all you
can do is delay for a while.  Perhaps the DNS service will suggest a safe
time.  If not, you'll have to start with a guess and adjust from there based
on your experience.  Choosing the right number - long enough but not
excessively long - can be hard, but applying it is easy.  Just add
`prop_delay=SIMPLE_DELAY_TIME` to the driver's initialization parameters,
and sewer's engine will add that many seconds of delay after the challenge
setup returns before it signals the ACME server to validate those
challenges.

**CLI option --p_opt prop_delay=... is available for all drivers since 0.8.3**

## API support or can check: use a timeout

If the DNS service gives you a way to check that the propagation is
complete, or if there are not too many authoritative servers (viz., not an
anycast system), you can use that actual check (implemented in the driver's
`unpropagated` method) and the engine will run that check until it succeeds
or until a timeout you specify is exceeded.  However the check is being
done, you setup the timeout by adding `prop_timeout=MAX_WAIT_TIME` to the
driver parameters.  If you know that it takes at least some minimum time to
propagate, you may also pass `prop_delay` to make the engine delay that long
before it starts checking.  And there's a delay between checks that has a
hopefully sensible default, but which you can adjust if necessary through
the `prop_sleep_times` parameter.

**no drivers implement `unpropagated` as of 0.8.3**

## You probably don't need to change `prop_sleep_times`

Unless you do, but if it's not obvious, just leave it.

This parameter defines the lengths of sleeps the engine will add following a
call to `unpropagated` that reports not ready.  As an optional parameter
passed to the driver, `prop_sleep_times` can be an integer number of seconds
or a list or tuple of such delays which will be used in order.  The final
value in the sequence will be reused indefinitely.

Example: the default value is (1, 2, 4, 8) which provides an exponential
backoff up to an 8 second delay, then sticks there.  _[the values could
change - it's just what seemed reasonable to me]_  So if there's no delay,
and the check call takes no measurable time (and reports not ready each
time), it will look something like this with `prop_timeout=20`:

| time | action |
| ---: | --- |
| 0 | call unpropagated, sleep(1) |
| 1 | call unproagagted, sleep(2) |
| 2 | call unpropagated, sleep(4) |
| 6 | call unpropagated, sleep(8) |
| 14 | call unpropagated, sleep(8) |
| 22 | call unpropagated, timeout! |

This shows both the last value repeating and the way the timeout and sleeps
interact.  The check for timeout is done only AFTER a call to unpropagated
AND the chance to exit with success if it finally reports the challenges are
ready.  So the timeout isn't a hard maximum time, but it's bounded to be no
more than one sleep interval (plus actual time to run `unpropagated`, of
course) over `prop_timeout`.

## Other Notes and Advanced Use

These values are setup through the Provider on the reasonable assumption
that they will vary most directly with the choice of service provider, so
the individual drivers are best suited to provide sensible defaults where
appropriate (and possible!).  Sewer's engine implements the delay and check
loop (with timeout) because the mechanism is the same for all providers (and
may be useful for other than the DNS-based challenges for which it has been
implemented).

If you are using sewer as a library and find that you can make a better
estimate of the propagation after the driver is setup (perhaps using a
service-specific method to access part of the service's API or run some
tests), you could adjust those parameters through the same-named attributes
on the Provider instance.  This is solidly in the categories of don't do it
unless you're sure you need to, and be prepared to own both the pieces if
you break it!

## Could this be used with non-DNS drivers?

Yes!  I have no experience with http-01 in any setting where such a delay
might be needed, but the mechanism is implemented in sewer's engine, and all
that needs be done is to setup the parameters (and implement unpropagated in
the driver if using more than just `prop_delay`) as described above and
there you go!
