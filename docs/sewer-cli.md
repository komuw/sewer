# Sewer's user command (so many --options!)

The `sewer-cli` command (sometimes just `sewer`, comes from
sewer/cli.py) is still a good vehicle for creating or renewing a single
certificate.  Simple cases may need only a few --options, but as time goes
by there are more possibilities, and more tunable parameters, that will be
needed for some uses.  The official doumentation of the options that
`sewer-cli` supports remains the output from running `sewer-cli --help`, but
that can be rather terse.  Here we will discuss what the options are and why
they are needed, especially some recently [or soon-to-be!] added options.

## sewer-cli General Options

--version

--log_level

--acme_timeout _seconds_
> Used to adjust the timeout applied to all requests to the ACME server. 
The default of 7 seconds is often enough, but if you have a slow or lossy
path to the ACME endpoint you may need to increase this.  _added by #188 in
pre-0.8.3; reworked from older #154 from @menduo_

## Account Options

Before doing anything else, you have to register an ACME account.  Without
any other options, `sewer-cli` will generate a new random key, use the
public part to register (including the e-mail address if you provided one),
and use that key for signing the ACME protocol messages to create the
specified certificate.  If you have an existing key you can use that
_provided_ it has already been registered with the ACME endpoint. 
**`sewer-cli` does not currently provide any way to use your unregistered
key in the ACME protocol.**

After the certificate has been created and downloaded, the account key
`sewer-cli` used will be saved alongside the certificate and certificate
key.  After this,the new account key is registered with the ACME endpoint
and may be used for future certificate requests using `--account_key`.

--account_key _filepath_
> Filepath to existing, already registered ACME account key.  Default is to
create a new key and register it.

--email _email_address_

--action "run"|"renew"
> Obsolescent.  Has no affect other than the word used in one message text.
Whether to create a server key and certificate de novo or reuse the existing
server key (the only thing that CAN be reused) depends only on whether
--certificate_key is given.  Default is "renew".

## ACME Options

--endpoint "production"|"staging"
> Default is "production", viz., issue a legitimate certificate.  Use
"staging" for testing!

## Provider Options

The only provider option used to be --dns.  In the near future, that will be
replaced by --provider, which from the outside looks like a cosmetic change,
but under the hood it will replace a lot of duplicative code & manual
configuration of providers with a catalog (and, of course, some new code). 
Because this will be somewhat disruptive, it has been held off until 0.9.

Some new features have been added, and more will be enabled in 0.9.  In
brief:

> --prop_delay is accepted and works in 0.8.3

> --alias_domain is accepted and warns that it doesn't work in 0.8.3.  It's a
warning because it CAN work with a provider that implements aliasing, there
just aren't any in sewer yet.

> --prop_timeout and --prop_sleep_times are left out of the interface for now
because they require implementation of part of the new provider interface.

### Provider configuration

--dns **name**
> Select the named provider.

### Waiting for the Network

There are two sorts of things for which we have to wait: the ACME server
(see --acme_timeout) and the service provider (especially DNS propagation
across a global anycast service).  Although these are USED in the core
engine code, they are SET through the driver.  The reasoning is that the
driver is the only part of sewer that might sensibly "know" what sensible
defaults for its service provider might be, and what features are available. 
So eg., although `prop_timeout` is available to all drivers, legacy DNS
drivers might want to issue a warning if it is specified since (unless
they're updated) they do not support the prop_timeout mechanism.

--prop_delay _seconds_
> Adds a fixed delay after the challenge response have all been setup to
allow the challenge to propagate before any other processing; the default is
no delay.  This is the simplest of the propagation waiting methods, and the
only one available to ~~unmodified~~ minimally modified legacy DNS drivers
such as those in 0.8.3.

--prop_timeout _seconds_
> Activates the active propagation checks and sets the timeout for that
process; default is to not do these checks.  This requires an implementation
of the driver `unpropagated` method to be useful.  Legacy DNS drivers
inherit a null implementation which always reports _all are ready_ which
short-circuits this process.  _to be added when there's driver support_

--prop_sleep_times _seconds,seconds,..._
> Comma-separated list of integer number of seconds to sleep after the
first, second, ...  _not all ready_ response from the driver's
`unpropagated` method.  The last value is re-used after the list has been
used up.  Default is "1,2,4,8".  _to be added when there's driver support_

### DNS Provider configuration

--alias_domain _alias_domain_
> Configure an alternate DNS domain in which the challenge responses will be
placed.  See [docs/Aliasing.md](Aliasing) for details.  **Legacy DNS
providers accept this, but require further modification to actually apply
the aliasing that's supported by their parent classes.**

## Certificate info

--domain **CN-name**
> The primary identity for the certificate.  REQUIRED, no default.  CN-name
is also used to form the default names for a number of files.

--alt_domains _SAN-name ..._
> List of alternate identities to be included in the certificate.  Not quite
what pedants would call "SAN", since this should NOT include the CN-name. 
Multiple identities may be given, and sewer-cli will take all parameters
(aka words) as SAN-names until it encounters another double-dash word. 
Default is an empty list.

--out_dir _dirpath_
> Set directory where the certificate and key files will be stored.  Default
is to use the current working directory where sewer was run.

--certificate_key _filepath_
> Full path to your [existing] certificate key.  As with the account_key, if
this is not specified, a new key will be created and used (in the
certificate).  Has a similar effect to certbot's --reuse-key (sp?).

--bundle_name _basename_
> Base name to use for output file, eg., out_dir/basename.{account.key,crt,key}
Default is to use the CN-name
