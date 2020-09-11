# Wildcard Certificates

Since 0.8.2, sewer should be able to request and receive simple wildcard
certificates using any of the DNS drivers.  In earlier versions there was an
eccentric re-naming of wildcard targets in the core logic which the drivers
would, sometimes unreliably, remove.  _tl;dr: before 0.8.2 it depended on the
driver._

## One issue remains in 0.8.3

Certificates with a wildcard CN name, eg., `domain=*.example.com`, are valid
for all and only the immediate sub domains of example.com.  They do NOT
validate for example.com itself, which may come as a surprise if you have
used some other (commercial?) providers, as they may silently add the
naked domain as described below.

To create such "wildcard-plus" certificates in sewer, you would still use
`domain=*.example.com`, then add `alt_domains=example.com`.  Sewer itself,
both through sewer-cli as well as the library interface (Client), is fully
capable of handling this.  The issue arises when publishing the challenge
response.  To a DNS ([1](#footnote1)) driver, this will appear as two
different TXT values for the same name (in this case "example.com"). 
Traditional DNS systems (inevitable eg.: bind) have no problem with having
multiple TXT records like this, but many DNS service providers are using
very different software.  To be honest, the problem some of sewer's drivers
have with this may be in the service provider's core system or just in their
API layer.  But we have had a problem using those APIs when setting up such
wildcard-plus-naked-domain certificate's validations, and from here on the
outside we can only deal with them one by one.

<span id="footnote1">(1)</span> HTTP challenges don't have this issue
because each challenge uses a unique file name/URL component.

> There is a general fix that OUGHT to be possible: have sewer's core logic
recognize cases where such "duplicate" challenges exist, and if the driver
doesn't announce itself capable of handling it, use a multi-step process to
publish a non-overlapping subset of the challenges, wait for propagation,
respond to the ACME server, and wait for the challenges to be validated,
then remove the subset; then repeat the whole process for the "duplicate"
validation.  For now, my (mmaney) "plan" is to continue helping driver
authors fix the drivers they're familiar with as a bug is reported (and try
to talk them into migrating to the new-model interface, of course!).
