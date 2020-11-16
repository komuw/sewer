# Aliasing for ACME Validation

The idea is presented (for dns-01 authorizations) in [an article at
letsencrypt.org](https://letsencrypt.org/2019/10/09/onboarding-your-customers-with-lets-encrypt-and-acme.html)
which shows an example of DNS aliasing and describes what was likely the
original motivation - a hosting provider running the certificate process on
behalf of his customers.  Like all DNS aliasing, it uses a CNAME at the
canonical name `_acme-challenge.domain.tld` to redirect the ACME server to a
different fqdn that is more convenient for provisioning of the validation
responses.  I'm not going to try to convince you that you should use
aliasing, because if you need it you probably already know that, or at least
know that the process isn't working smoothly as-is.

The `alias` option in sewer is available to drivers that derive from
`DNSProviderBase`.

>Added in 0.8.3: `--p_opts alias=...`, but legacy drivers don't take
advantage of the aliasing support in their parent classes yet.

## Isn't aliasing just for DNS?

No.  HTTP has had, as a side effect of common web server and client behavior,
a kind of aliasing since the very beginning of ACME.  Usually it's
convenient enough to provision the validation at the canonical
`/.well-known/acme-challenge/<token>` location.  But if it isn't, either
`acme-challenge` or `.well-known` can be mapped (by server configuration or
externally by symlink, usually) to some other location.  If it's desired to
serve the validation file from some other domain or server altogether, an
HTTP redirect can often be used (and that's also a third way to place the
file elsewhere within the web server's accesible filesystem).

The RFC says that (for http-01 challenges) the ACME server "SHOULD follow
redirects", which would allow for an analogous aliasing.  Lets' Encrypt's
servers [do follow redirects and
CNAMES](https://letsencrypt.org/docs/challenge-types/).

So aliasing can be used with HTTP validations, though it's probably less
often needed since the privilege needed to directly configure the canonical
response file is likely to be the same (or even less) than that needed to
setup the new certificate.  And it's possible that you've already used it
without thinking of it as _aliasing_ because it uses such basic HTTP
behavior (and so needs no support from sewer).

## Preparing for DNS aliasing

The first thing which you must have is a way to manage DNS TXT records.  In
fact, you need to be able to control both the real domain's records (in
order to setup the CNAME entries, but that's something that needs be done
only once) as well as managing the alias domain records through the
service-specific driver.  Generally, expect to need a new-model driver
rather than an existing legacy driver, on the assumption that it's not much
more work to migrate the legacy driver to the new interface while adding the
alias support.  I have my fingers crossed, at any rate...

With alias-capable driver in hand, you then setup CNAME records for every
DNS name that you wish to use with the alias domain.  In traditional zone
file form that might look something like this [excerpt]:

    ; existing record for your web or other server
    name.example.com.                  IN  A     111.222.333.444

    ; then add the CNAME at the ACME-prefixed name
    _acme-challenge.name.example.com.  IN  CNAME name.example.com.alias.org

In online domain editors, the names are usually given without the full
domain suffix that's shown here (example.com).  The A record (or it could be
a CNAME) for `name.example.com` that directs to your server is shown as an
example here.
The added CNAME record is the redirect from the conventional ACME challenge
DNS name, pointing to the TXT record in the alias domain.  When it sees that
CNAME, the ACME server will proceed to look for the challenge's TXT record
at `name.example.com.alias.org`.  Since the alias-aware driver will have
setup that TXT record, the server will retrieve it and validate your right
to issue for `name.example.com`.

Note that the alias domain can be ANY valid domain that you can manage.  In
particular, it can be in a different tld (as shown here) or a different
domain in the same tld, or even in a sub-domain (eg. 
`validation.example.com`) of the target's domain that has been delgated to
that more convenient DNS server.  And you can setup aliased TXT challenge
records for names from any number of _real_ domains as long as the CNAME
redirects can be provisioned.

## Using DNS aliases in sewer

This is really pretty short & sweet.
All that's needed, once the setup is done, is to pass `alias=alias.org` to
the alias-supporting driver when it's created.
From the command line, that's `--p_opts alias=alias.org`.
