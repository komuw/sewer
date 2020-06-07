## ACME, RFCs, and confusion, oh my!

ACME grew out of early, ad-hoc procedures designed to let CAs issue large
numbers of certificates with low overhead.  As described in RFC855, these
would go something like this:

> * Generate a PKCS#10 [RFC2986] Certificate Signing Request (CSR).
> * Cut and paste the CSR into a CA's web page.
> * Prove ownership of the domain(s) in the CSR by one of the following methods:
>     + Put a CA-provided challenge at a specific place on the web server
>     + Put a CA-provided challenge in a DNS record corresponding to the target domain
>     + Receive a CA-provided challenge at (hopefully) an administrator-controlled email 
>       address corresponding to the domain, and then respond to it on the CA's web page
> * Download the issued certificate and install it on the user's web server
>
> With the exception of the CSR itself and the certificates that are
> issued, these are all completely ad hoc procedures and are
> accomplished by getting the human user to follow interactive natural
> language instructions from the CA rather than by machine-implemented
> published protocols.

HTTP validation was the first mechanism, matching the first method of
proving ownership in the above.  The rest of what
[Let's Encrypt](https://letsencrypt.org)
added was automating the process (and rearranging it a bit, having the proof
of control happen before the CSR, etc.).  Years later, the IETF standardized
the ACME protocol, and there are other variants that have been (or will be)
standardized.

## RFC8555

The [IETF](https://www.ietf.org/) accepted(?) and published
[RFC8555](https://tools.ietf.org/html/rfc8555) defining the ACME protocol
for http-01 and dns-01 validations of dns-name authorizations.  These are
the sort of ACME authorizations that we usually think of, and which sewer
works with.  The RFC was published in the spring of 2019, but it wasn't
until near the end of that year that Let's Encrypt adopted the full v.2 on
only their *staging* server.  There's some elaborate and, from what I can
make out, often-shifting schedule for various partial transitions, but I'm
not going to try to make sense of them.  As of the beginning of 2020, the
only immediate effect on sewer was that one could no longer run it against
the *staging* server.  The next big change is when that same restriction is
rolled out on LE's *production* server late in the year.  Since sewer
v0.8.2, which implemented the final RFC8555 protocol at least well enough to
work with LE's server implementation, our tl;dr is just this:

> If you get a failure running an older version of sewer, get v0.8.2 or
> later.  This is a known problem: v0.8.2 is the fix.
