import subprocess

from .common import BaseDns


class UnboundSsh(BaseDns):
    """
    Working demo of using aliasing with legacy DNS model.

    This punts the authorization issue to the ssh command.  For unattended
    operation you'd need to run this with the key preloaded in ssh-agent or
    some equivalent.

    CLI options with alias (requires latest pre-0.8.3 code):
        --provider unbound_ssh --p_opts alias=... ssh_des=user@host

    Client usage:
        provider = UnboundSsh(ssh_des="user@host", alias="...")
        acme = client.Client(domain="host.your.domain", provider=provider, ...)
        certificate = acme.cert()
        ...
    """

    def __init__(self, *, ssh_des, **kwargs):
        """
        ssh_des is a REQUIRED keyword option that specifies the "destination"
        argument for making the SSH connection (see ssh(1)).  It is ASSUMED
        that the remote login has access to unbound's key so that it can run
        unbound-control to update the alias zone.
        """

        super().__init__(**kwargs)
        self.ssh_des = ssh_des

    def create_dns_record(self, host_fqdn, acme_challenge):
        self.manage_dns_record(host_fqdn, acme_challenge, "add")

    def delete_dns_record(self, host_fqdn, acme_challenge):
        self.manage_dns_record(host_fqdn, acme_challenge, "del")

    def manage_dns_record(self, host_fqdn, acme_challenge, cmd):
        """
        The first line of code here is really the whole of the aliasing demo - everything
        else is just the scaffolding to make this work in my quirky environment.  :-)

        NB: faking the challenge dict like this is potentially fragile.  Much better to
        migrate the legacy DNS driver to the new model if possible!
        """

        fqdn = self.target_domain({"ident_value": host_fqdn})

        update_cmd = unbound_command(cmd, fqdn, acme_challenge)
        res = subprocess.run(("ssh", self.ssh_des, "unbound-control -- ", update_cmd))
        if res.returncode != 0:
            raise RuntimeError(
                "FAILURE (%s): unbound command failed:\n  %s" % (res.returncode, res.args)
            )


# DO # NOT # USE # @classmethod # just to hide the function in the class.  Namespaces are great!


def unbound_command(cmd, fqdn, acme_challenge):
    if cmd == "add":
        return "local_data %s. 300 IN TXT '%s'" % (fqdn, acme_challenge)
    if cmd == "del":
        return "local_data_remove %s." % (fqdn,)

    raise ValueError("Unrecognized command to unbound_command: %s" % (cmd,))
