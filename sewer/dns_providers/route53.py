import collections

try:
    route53_dependencies = True
    import boto3
    from botocore.client import Config
except ImportError:
    route53_dependencies = False

from . import common


# most code of this class is copy from certbot's route53 dns plugin.
class Route53Dns(common.BaseDns):
    ttl = 10
    connect_timeout = 30
    read_timeout = 30

    def __init__(self, access_key_id=None, secret_access_key=None):
        if not route53_dependencies:
            raise ImportError(
                """You need to install Route53Dns dependencies. run; pip3 install sewer[route53]"""
            )

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
        else:
            # let boto3 find credential
            # https://boto3.readthedocs.io/en/latest/guide/configuration.html#best-practices-for-configuring-credentials
            self.r53 = boto3.client("route53", config=self.aws_config)

        self._resource_records = collections.defaultdict(list)

        super(Route53Dns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        challenge_domain = "_acme-challenge" + "." + domain_name + "."
        return self._change_txt_record("UPSERT", challenge_domain, domain_dns_value)

    def delete_dns_record(self, domain_name, domain_dns_value):
        challenge_domain = "_acme-challenge" + "." + domain_name + "."
        return self._change_txt_record("DELETE", challenge_domain, domain_dns_value)

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

    def _change_txt_record(self, action, domain_name, domain_dns_value):
        zone_id = self._find_zone_id_for_domain(domain_name)

        rrecords = self._resource_records[domain_name]
        challenge = {"Value": '"{0}"'.format(domain_dns_value)}
        if action == "DELETE":
            # Remove the record being deleted from the list of tracked records
            rrecords.remove(challenge)
            if rrecords:
                # Need to update instead, as we're not deleting the rrset
                action = "UPSERT"
            else:
                # Create a new list containing the record to use with DELETE
                rrecords = [challenge]
        else:
            rrecords.append(challenge)

        response = self.r53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "certbot-dns-route53 certificate validation " + action,
                "Changes": [
                    {
                        "Action": action,
                        "ResourceRecordSet": {
                            "Name": domain_name,
                            "Type": "TXT",
                            "TTL": self.ttl,
                            "ResourceRecords": rrecords,
                        },
                    }
                ],
            },
        )
        return response["ChangeInfo"]["Id"]
