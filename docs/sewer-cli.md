# Sewer's use command (so many --options!)

The traditional `sewer-cli` command (sometimes just `sewer`, comes from
sewer/cli.py) is still a good vehicle for creating or renewing a single
certificate.  Simple cases may need only a few --options, but as time goes
by there are more possibilities, and more tunable parameters, that will be
needed for some uses.  The official doumentation of the options that
`sewer-cli` supports remains the output from running `sewer-cli --help`, but
that can be rather terse.  Here we will discuss what the options are and why
they are needed, especially some recently [or soon-to-be!] added options.

## sewer-cli Options

--version

--log_level

## Account Options

--account_key _filepath_
> Identifies your [existing] ACME account key file.  If not specified, sewer
will create a new account key, unique to this execution, and register it.

--email _email_address_

--action **"run"|"renew"**
> The only effect this has is on whether to register the account key de novo
(for run) or with the existing-only ACME option (for renew, of course). 
> _need to verify this?_

## ACME Options

--endpoint "production"|"staging"

## Provider Options

### Provider configuration

--dns **name**
> Select the named provider.  --dns is the traditional name; --provider is a
new (pre-0.8.3 ?) alias for it, and currently works the same.

### Waiting for the Network

There are two sorts of things for which we have to wait: the ACME server
and the service provider (especially DNS propagation across a global anycast
service).  Although these are USED in the core engine code, they are SET
through the driver.  The reasoning is that the driver is the only part of
sewer that might sensibly "know" what sensible defaults for its service
provider might be, and what features are available.  So eg., although
`prop_timeout` is available to all drivers, legacy DNS drivers might want to
issue a warning if it is specified since (unless they're updated) they do
not support the prop_timeout mechanism.

--acme_timeout _seconds_
> Used to adjust the timeout applied to all requests to the ACME server. 
The default of 7 seconds is often enough, but if you have a slow or lossy
path to the ACME endpoint you may need to increase this.  _added by #188 in
pre-0.8.3; reworked from older #154 from @menduo_

--prop_delay _seconds_
> Adds a fixed delay after the challenge response have all been setup to
allow the challenge to propagate before any other processing; the default is
no delay.  This is the simplest of the propagation waiting methods, and the
only one available to unmodified legacy DNS drivers.  _to be added
RealSoonNow, Jun 29 2020_

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


### Certificate info

--domain **CN-name**
> The primary identity for the certificate.  REQUIRED, no default.  CN-name
is also used to form the default names for a number of files.

--alt_domains _SAN-name ..._
> List of alternate identities to be included in the certificate.  Not quite
what pedants would call "SAN", since this should NOT include the CN-name. 
Multiple identities may be given, and sewer-cli will take all parameters
(aka words) as SAN-names until it encounters another double-dash word. 
Default is an empty list.

--alias_domain _alias_domain_
> Configure an alternate DNS domain in which the challenge responses will be
placed.  See [docs/Aliasing.md](Aliasing) for details.  _core and a
demonstartion driver, but no existing legacy drivers, have support in
pre-0.8.3.  --alias_domain option to be added RealSoonNow.__

--out_dir _dirpath_
> Set directory where the certificate and key files will be stored.  Default
is to use the current working directory where sewer was run.

--certificate_key _filepath_
> Full path to your [existing] certificate key.  As with the account_key, if
this is not specified, a new key will be created and used (in the
certificate).

--bundle_name _basename_
> Base name to use for output file, eg., out_dir/basename.crt _? need to
check this one?_

