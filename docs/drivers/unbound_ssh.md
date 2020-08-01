## unbound_ssh legacy DNS driver

A working, if somewhat quirky, driver to setup challenges in local data of
the [unbound](https://nlnetlabs.nl/projects/unbound/about/) caching
resolver.  As the name suggests, it relies upon ssh to provide an
authenticated connection the server; inside that connection the
`unbound-control` program is used to add and remove the records.  The driver
does NOT handle the login authorization, assuming that it is running
interactively and ssh will prompt for your input, or that a key agent (eg.,
ssh-agent) is active to supply the cryptographic credentials.  That's the
_somewhat quirky_ part!

### `__init__(self, *, ssh_des, **kwargs)`

There is one REQUIRED parameter, `ssh_des`, which is the login target, such
as acme_user@ns1.example.com.  This is simply passed to the ssh command,
along with the `unbound-control` commands to be executed on the destination
machine.

### Driver features

unbound_ssh supports the `alias` parameter.

Only `prop_delay` is supported; there is no custom `unpropagated` method.

### Usage

From the command line:

    python3 -m sewer ... --provider=unbound_ssh --p_opt ssh_des=acme@ns.example.com ...

From custom code:

    from sewer.dns_providers.unbound_ssh import UnboundSSH

    provider = UnboundSSH(ssh_des="acme@ns.example.com", alias="validation.example.com")
    ...

### Bugs

Sadly, This was written using the old paradigm where both the module name
and the class name were more-or-less the same name aside from
capitalization... and often less predictable changes.  Should have been
unbound_ssh.Provider ...

The `unbound-control` commands generated could be run locally with not very
much change to the driver.  Perhaps that will become part of a demonstration
of some different features in the future.
