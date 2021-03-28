from sewer.auth import ChalListType, ErrataListType, DNSProviderBase
from sewer.lib import dns_challenge, SewerError

from windowsdnsserver.command_runner.powershell_runner import PowerShellRunner
from windowsdnsserver.dns.dnsserver import DnsServerModule


class WinDNS(DNSProviderBase):
    def __init__(self, zone=None, power_shell_path=None, **kwargs):
        super().__init__(**kwargs)

        if not isinstance(zone, str) or not zone:
            raise ValueError("windns requires a string value for the zone argument")

        self.zone = zone

        runner = None
        if power_shell_path:
            runner = PowerShellRunner(power_shell_path)

        self.dns = DnsServerModule(runner)

        if not self.dns.is_dns_server_module_installed():
            raise SewerError(
                "It seems that, the DNSServer module is not installed. Please check the windns documentation.."
            )

    def setup(self, challenges: ChalListType) -> ErrataListType:
        for challenge in challenges:
            if not self.alias:
                self._validate_domain_contains_zone(challenge)

            name, txt_value = self._get_dns_name_and_text_for_challenge(challenge)
            self.dns.add_txt_record(self.zone, name, txt_value)

        return []

    def unpropagated(self, challenges: ChalListType) -> ErrataListType:
        return []

    def clear(self, challenges: ChalListType) -> ErrataListType:
        for challenge in challenges:
            name, txt_value = self._get_dns_name_and_text_for_challenge(challenge)
            self.dns.remove_txt_record(self.zone, name, txt_value)

        return []

    # --- Challenge ---

    def _get_dns_name_and_text_for_challenge(self, challenge):
        name = self._extract_sub_domain_from_challenge(challenge)
        txt_value = dns_challenge(challenge["key_auth"])

        return name, txt_value

    def _validate_domain_contains_zone(self, challenge):
        domain = self.target_domain(challenge)
        if self.zone not in domain:
            raise SewerError(
                "Domain must contains zone, domain: [%s], zone: [%s]" % (domain, self.zone)
            )

    def _extract_sub_domain_from_challenge(self, challenge):
        """
        zone: example.com, domain: example.com ---> sub domain is ""

        zone: example.com, domain: test.asd.example.com ---> sub domain is "test.asd"

        zone: asd.example.com, domain: test.asd.example.com ---> sub domain is "test"
        """
        domain = self.target_domain(challenge)

        sub_domain_index = domain.rfind(".%s" % self.zone)
        return domain[0:sub_domain_index]
