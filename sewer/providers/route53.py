import boto3  # type: ignore
from botocore.client import Config  # type: ignore

from typing import Dict, Sequence

from ..auth import ErrataItemType, DNSProviderBase
from ..lib import dns_challenge


class Route53Dns(DNSProviderBase):
    ttl = 10
    connect_timeout = 30
    read_timeout = 30
    prop_timeout = 120
    prop_sleep_times = [2]

    def __init__(self, access_key_id=None, secret_access_key=None, client=None, **kwargs):
        if (access_key_id or secret_access_key) and client:
            raise RuntimeError("Pass keys OR preconfigured client, not both")

        self.aws_config = Config(
            connect_timeout=self.connect_timeout, read_timeout=self.read_timeout
        )
        if access_key_id and secret_access_key:
            # use user given credential
            self.r53 = boto3.client(
                "route53",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                config=self.aws_config,
            )
        elif client:
            # Use the client passed in from the caller.
            self.r53 = client
        else:
            # let boto3 find credential
            # https://boto3.readthedocs.io/en/latest/guide/configuration.html#best-practices-for-configuring-credentials
            self.r53 = boto3.client("route53", config=self.aws_config)
        super().__init__(
            **kwargs, prop_timeout=self.prop_timeout, prop_sleep_times=self.prop_sleep_times
        )

    def setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        self._process_challenges(challenges, "UPSERT")
        return []

    def unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        unready = []
        for chal in challenges:
            response = self.r53.get_change(Id=chal["change_id"])
            if response["ChangeInfo"]["Status"] != "INSYNC":
                unready.append(("unready", "still waiting for propagation", chal))
        if len(unready) == 0:
            return ("", [])
        else:
            return ("unready", unready)

    def clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        self._process_challenges(challenges, "DELETE")
        return []

    def _process_challenges(
        self, challenges: Sequence[Dict[str, str]], action
    ) -> Sequence[ErrataItemType]:
        unique_domains = {}
        for chal in challenges:
            target_domain = self.target_domain(chal)
            if unique_domains.get(target_domain) is None:
                unique_domains[target_domain] = {"values": [], "challenge_indices": []}
            unique_domains[target_domain]["values"].append(
                {"Value": '"{0}"'.format(dns_challenge(chal["key_auth"]))}
            )
            unique_domains[target_domain]["challenge_indices"].append(challenges.index(chal))
        for domain, challenge_info in unique_domains.items():
            self._apply_challenge_change(challenges, action, domain, challenge_info)

    def _find_zone_id_for_domain(self, domain):
        """Find the zone id responsible a given FQDN.
        That is, the id for the zone whose name is the longest parent of the
        domain.
        """
        paginator = self.r53.get_paginator("list_hosted_zones")
        zones = []
        target_labels = domain.rstrip(".").split(".")
        for page in paginator.paginate():
            for zone in page["HostedZones"]:
                if zone["Config"]["PrivateZone"]:
                    continue

                candidate_labels = zone["Name"].rstrip(".").split(".")
                if candidate_labels == target_labels[-len(candidate_labels) :]:
                    zones.append((zone["Name"], zone["Id"]))

        if not zones:
            raise RuntimeError("Unable to find a Route53 hosted zone for {0}".format(domain))

        # Order the zones that are suffixes for our desired to domain by
        # length, this puts them in an order like:
        # ["foo.bar.baz.com", "bar.baz.com", "baz.com", "com"]
        # And then we choose the first one, which will be the most specific.
        zones.sort(key=lambda z: len(z[0]), reverse=True)
        return zones[0][1]

    def _apply_challenge_change(self, challenges, action, domain, challenge_info):
        zone_id = self._find_zone_id_for_domain(domain)
        changeset = {
            "Comment": "certbot-dns-route53 certificate validation " + action,
            "Changes": [
                {
                    "Action": action,
                    "ResourceRecordSet": {
                        "Name": domain,
                        "Type": "TXT",
                        "TTL": self.ttl,
                        "ResourceRecords": challenge_info["values"],
                    },
                }
            ],
        }
        response = self.r53.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=changeset)
        for index in challenge_info["challenge_indices"]:
            challenges[index]["change_id"] = response["ChangeInfo"]["Id"]
        return
