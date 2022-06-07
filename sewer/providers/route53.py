import collections
import time

import boto3  # type: ignore
from botocore.client import Config  # type: ignore

from typing import Dict, Sequence

from ..auth import ErrataItemType, DNSProviderBase
from ..lib import dns_challenge


class Route53Dns(DNSProviderBase):
    ttl = 10
    connect_timeout = 30
    read_timeout = 30
    propagate_timeout = 120

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

        self._resource_records = collections.defaultdict(list)
        super().__init__(**kwargs)

    def setup(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        self._process_challenges("UPSERT", challenges)
        return []

    def unpropagated(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        return []

    def clear(self, challenges: Sequence[Dict[str, str]]) -> Sequence[ErrataItemType]:
        self._process_challenges("DELETE", challenges)
        return []

    def _process_challenges(self, action, challenges):
        changeset_batches = self._create_changeset_batches(action, challenges)
        change_id = self._apply_changeset_batches(action, changeset_batches)
        self._wait_for_propagation(change_id)

    def _create_changeset_batches(self, action, challenges):
        changeset_batches = {}
        for chal in challenges:
            name = self.target_domain(chal)
            value = '"{0}"'.format(dns_challenge(chal["key_auth"]))
            zone_id = self._find_zone_id_for_domain(name)
            if changeset_batches.get(zone_id) is None:
                changeset_batches[zone_id] = {}

            if changeset_batches[zone_id].get(name) is None:
                changeset_batches[zone_id][name] = {
                    "Action": action,
                    "ResourceRecordSet": {
                        "Name": name,
                        "Type": "TXT",
                        "TTL": self.ttl,
                        "ResourceRecords": [
                            {
                                "Value": value,
                            }
                        ],
                    },
                }
            else:
                changeset_batches[zone_id][name]["ResourceRecordSet"]["ResourceRecords"].append(
                    {"Value": value}
                )
        return changeset_batches

    def _wait_for_propagation(self, change_ids):
        for change_id in change_ids:
            for i in range(0, self.propagate_timeout):
                response = self.r53.get_change(Id=change_id)
                if response["ChangeInfo"]["Status"] == "INSYNC":
                    return
                if i >= self.propagate_timeout:
                    raise RuntimeError("Waited too long for Route53 DNS propagation")
                # Only used to avoid being ratelimited checking for status
                time.sleep(1)

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

    def _apply_changeset_batches(self, action, changeset_batches):
        change_ids = []
        for zone_id, changeset_batch in changeset_batches.items():
            response = self.r53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    "Comment": "certbot-dns-route53 certificate validation " + action,
                    "Changes": list(changeset_batch.values()),
                },
            )
            change_ids.append(response["ChangeInfo"]["Id"])
        return change_ids
