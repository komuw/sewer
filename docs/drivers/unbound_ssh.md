## unbound_ssh legacy DNS driver

A working, if somewhat quirky, driver to setup challenges in the unbound
server, using ssh to connect to an account able to run unbound-control
commands.  The driver does NOT handle the login authorization, assuming that
it is running interactively and ssh will prompt for your input, or that a
key agent (eg., ssh-agent) is active to supply the cryptographic
credentials.

### `__init__(self, *, ssh_des, **kwargs)`

There is one REQUIRED parameter, `ssh_des`, which is the login target, such
as acme_user@ns1.example.com.  This is simply passed to the ssh command,
with the unbound-control commands passed as the command to execute remotely.

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
