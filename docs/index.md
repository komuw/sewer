## sewer, the ACME library and command-line client

A quick guide to the docs directory.
NB: much of this was written to document what I'd just done,
and as you might expect that led to quite a few _oh bother, that's not the
right way to do it_ moments.
After which sometimes the docs got revised and then the code;
other times the other way around; and these could iterate.

And sometimes the docs proved to be wrongly named, or split into parts.

And none of this is **done** changing yet.

- [UnifiedProvider.md](UnifiedProvider) was the first intentional thought
  doc.  It has been written and revised repeatedly since Alec's original
  http-01 changes got me thinking about how best to accomodate both, as well
  as other validation methods that were already RFCs or on their way.
- [unpropagated.md](unpropagated) was the first separate piece.  Begun as I was
  figuring out what to do, and changes upon changes here as well.  Heading
  towards being documentation of the implementation.
- [DNS-Propagation.md](DNS-Propagation) has become (is becoming?) the document
  about _what_ propagation means to the ACME process and _how_ we might
  manage it.  From the title you can tell it began when I was still thinking
  of propagation as DNS thing.
- [Aliasing.md](Aliasing), just renamed from DNS-Aliasing, so the contents must
  still be in flux, too.  Probably a lumpy blending of implementation and
  user notes, still.
- [ACME.md](ACME) A bit of history, a start on a technical essay, or ??? 
  Notes on various things related to ACME and Let's Encrypt's servers.
- [LegacyDNS.md](LegacyDNS) Documents the new-model shim (still named
  BaseDNS) that allows unmigrated Legacy DNS drivers to continue working. 
  Authors of any DNS module, Legacy or new, should review this... and,
  hopefully, migrate to or start anew as new-model Providers.
- [wildcards.md](wildcards) Notes about wildcard certificates - they should
  work for all drivers now! - and a special case where there are probably
  still issues.

And an even less stable (because it hasn't been coded yet!) peek at
something I'm calling [cloaca](preview/cloaca) for now.
