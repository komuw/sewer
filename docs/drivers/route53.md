## route53 - driver for AWS DNS service

### Command line use

route53 has never been wired into `sewer-cli`, and that hasn't really
changed in 0.8.3.  It does appear in the list of "known providers", but it
isn't usable, and raises an exception if named by `--provider`.

Adding that integration is on the list, but seeing as no one has complained
about this lack up to now it's nowhere near the top.  :-(

### Programmatic use

Apparently everyone using sewer's route53 has been rolling their own
wrapper, since it has only been available for such use to date.  There is a
patch to extend that Route53Dns.__init__ to allow additional AWS-specific
methods of authentication which I expect will ship in 0.8.3.
