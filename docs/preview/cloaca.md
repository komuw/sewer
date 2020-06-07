# Cloaca, aka sewer-cli-next?

_This is so preliminary that it hasn't been written yet.  A design essay in
a rambling style is all it is._

The design of the sewer-cli program is focused on getting one certificate
with no state (aside from the optionally reused account key) on disk.  I can
say from much personal experience that this is wonderful for doing ad-hoc
tests while changing the implementation, and it's workable even for getting
a handful of certificates (ah, shell script, how I both love and hate
thee...), but I've long thought about a better way - better, at least, for
how I'd like to handle certificate renewal.

## Shortcomings of sewer-cli

One thing that I kept tripping on was the apparent lack of a simple way to
setup a new account key for later use.  And strictly speaking, sewer-cli
just doesn't do that.  Enlightenment comes when you give proper
consideration to sewer-cli's scope - it gets only one certificate per
invocation, so you can harvest the one it created and reuse it later.  I
missed that because I was already looking to get several (three, IIRC)
certificates when I first started using sewer.

The other "issues" that come to mind are just limitations of the intended
scope of sewer-cli.  As mentioned above, I ended up doing some shell
scripting to work around _all those --options, some the same and some that
change for each certificate_.  And the other part I wanted to automate (and
felt less happy doing in a shell script for $REASONS) was getting the new
certificates installed after they were created.

So cloaca addresses these.

## The cloaca command

First change - the cloaca command takes, as its first, required, non-option
argument, the sub-command which selects the operation to carry out.  The
short list so far goes like this:

- account - create key, register, deregister, maybe transfer, others
- renew - with no options, renew & install (if configured) all certs in cloaca.ini

And more to come.  Plenty of operations are defined in RFC8555 which never
got into sewer-cli.  Goal will be to support all the operations in the RFC
that Let's Encrypt has implemented.

Second change - cloaca is more [config-driven](cloaca_config) than
--option-driven.  Which doesn't mean options won't be available, but maybe
not to the point of emulating sewer-cli's ability to renew one certificate
without any configuration.

_Okay, that's it for now.  Need to get some proof of concept code to see if
any of the untested ideas are more problematic than I believe._
