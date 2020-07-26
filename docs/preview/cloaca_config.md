# Configuration file for cloaca

_This is a pre-coding, let alone release, preview of a more config-driven
user command that's just starting to bubble in the crock pot here.  It could
end up being cli-next if it's practical to combine the two different
approaches in one.  Either way, it needs a less awkward name than cli-next. :-)_

Cloaca's configuration has been driven by a couple use cases.  If you have
only a single certificate, for one or a few identities (SANs), the
traditional option-driven CLI program is perhaps easier.  Cloaca is designed
for the case where several certificates are being managed together.  It also
adds installation support to get those certificates onto the servers. 
Somewhat to my surprise, it has ended up using the simple "ini" file format.

## Introductory examples

A minimal configuration for one certificate for test.example.com that just
leaves test.example.com.key and test.example.com.key sitting in the current
working directory:

    [cert_test.example.com]
    account_email = webmaster@example.com
    provider = demo_dns

This demonstrates an important convention: certificate sections are named by
prepending "cert_" to the domain identity.  The only other data it requires
to produce a new key and certificate, is the name of the Provider class that
will handle publishing the challenge responses.  As always, the driver's
auhtentication parameters are here assumed to be passed in through
environment variables (but they could be additional items in that section if
you like).

Now, let's add the promised installation to this example:

    [cert_test.example.com]
    account_email = webmaster@example.com
    provider = demo_dns
    install_transport = ssh
    install_ssh_to = root@test.example.com
    install_dir = /etc/apache2/ssl
    install_post_cmd = system restart apache2

Getting a little longer, and it glosses over how it gets the ssh key it will
need for the installation.  So what happens when we have multiple
certificates?

    [cert_default]
    account_key = account.key
    account_email = webmaster@example.com
    provider = demo_dns
    install_transport = ssh
    install_dir = /etc/apache2/ssl
    install_post_cmd = systemctl restart apache2

    [cert_test.example.com]
    install_ssh_to = root@test.example.com

    [cert_example.com]
    SAN = www.example.com
    install_ssh_to = hostmaster@www.example.com

    [cert_webmail.example.com]
    install_ssh_to = postmaster@webmail.example.com
    install_dir = /etc/certificates
    install_post_cmd = systemctl restart dovecot

There's a reason this avoids the native [DEFAULT] section, which we'll come
back to later.

## Configuration Reference

All of the actual configuration options can appear in a certificate section. 
A certificate section is any section whose name is formed by prepending
"cert_" to the principle domain name (CN in certificate speak).  The
available keys:

- account_key = filepath to account key to use for this certificate
- account_email = what it says, obviously
- account_file = filepath to file with account key, email, and other info TBD
  (this might replace _key and _email, those coming as args to account creation?)
- provider = name of Provider class
- provider_KW = value, passed to class constructor as KW=value
- SAN = san1, san2, ...  comma-separated list of additional identifiers to add to certificate
- install_transport = name of method to use, eg., ssh, cp, ...
- install_ssh_to = user@fqdn for any ssh-based transport (also for post_cmd, etc)
- install_dir = path (should be absolute) to directory where new key & crt are installed
- install_post_cmd = command to be run after key is installed (to make it take effect)

As seen above, a [cert_default] section will be folded in to every [cert_CN]
section.  This is convenient for truly universal settings, but the `_method`
mechanism is preferred for settings that apply less universally.  In any
event, an explicit setting in [cert_CN] will always take precedence over
those injected from other sources.

### The `_method` Method

This allows a group of settings that are shared among some of the
certificates to be grouped and defined once, then included by name.  More or
less:

    [cert_default]
    account_key = account.key
    provider = demo_dns

    [install_apache2]
    transport = ssh
    dir = /etc/apache2/ssl
    post_cmd = systemctl restart apache2

    [cert_test.example.com]
    install_method = apache2
    install_ssh_to = root@test.example.com

    [cert_example.com]
    SAN = www.example.com
    install_method = apache2
    install_ssh_to = hostmaster@www.example.com

The mechanism finds keys of the form PREFIX_method = NAME and looks for
a section [PREFIX_NAME].  It then replaces the PREFIX_method item with
the items in that section after prepending PREFIX_ to each key.  So in the
above, each occurence of

    install_method = apache2

is replaced by items from [install_apache2] which become

    install_transport = ssh
    install_dir = /etc/apache2/ssl
    install_post_cmd = systemctl restart apache2

Which is much like what a [cert_default] section would do except it wouldn't
try to add the apache config items into certs that are for an nginx hosted
domain, say.  The `_method` method only injects the settings it's explicitly
asked to insert.
