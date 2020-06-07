# Wildcard Certificates

Since 0.8.2, sewer should be able to request and receive simple wildcard
certificates using any of the DNS drivers.  In earlier versions there was an
odd re-naming of wildcard targets that drivers would, sometimes unreliably,
remove - tl;dr: before 0.8.2 it depended on the driver.

One issue remains.  Certificates with a wildcard CN name, eg.,
*.example.com, are valid for all and only the immediate sub domains of
example.com.  They do NOT validate for the example.com domain itself, which
may come as a surprise if you have used some other (commercial?) providers,
as they sometimes just add the naked domain as decsribed below.

The trick is that you use *.example.com as the CN, and add the bare
example.com as a SAN (in sewer-cli terms: --domain *.example.com
--alt_domains example.com).  Sewer itself, both through sewer-cli as well as
the library interface (Client) is fully capable of handling this.  The catch
is in publishing the challenge response.  To the service-specific driver,
this will appear as two different TXT values for the same name (naked
example.com, since there are no wildcards in DNS).  Traditional DNS systems
(inevitable eg.: bind) have no problem with having multiple TXT records like
this, but many DNS service providers are using very different software.  To
be honest, as I don't use any of these myself, so I have no idea if the
problem some of sewer's drivers have with this are in the service provider's
core system or just their API layer.  But we have had a problem using those
APIs when setting up such wildcard-plus-naked-domain certificate's
validations, and from here on the outside we can only deal with them one by
one.

> There is a general fix that OUGHT to be possible: have sewer's core logic
recognize cases where such "duplicate" challenges exist, and if the driver
doesn't announce itself capable of handling it, use a multi-step process to
publish some of the challenges, wait for propagation, respond to the ACME
server, and wait for the challenges to be validated; then repeat the whole
process for the "duplicate" validation.  For now, my (mmaney) "plan" is to
continue helping driver authors fix the drivers they're familiar with as a
bug is reported (and try to talk them into migrating to the new-model
interface, of course!).
