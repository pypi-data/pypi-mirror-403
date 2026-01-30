import boto3
from botocore.exceptions import ClientError


def enrich(ec2s, region):
    ec2 = boto3.client("ec2", region_name=region)
    autoscaling = boto3.client("autoscaling", region_name=region)

    # Cache existing keypairs
    try:
        kp_resp = ec2.describe_key_pairs()
        existing_keypairs = {kp["KeyName"] for kp in kp_resp["KeyPairs"]}
    except ClientError:
        existing_keypairs = set()

    # Cache all EIPs
    addresses = ec2.describe_addresses().get("Addresses", [])

    for e in ec2s:
        # -------------------------
        # Instance details
        # -------------------------
        resp = ec2.describe_instances(InstanceIds=[e.instance_id])
        inst = resp["Reservations"][0]["Instances"][0]

        # -------------------------
        # ASG membership (check if instance is managed by ASG)
        # -------------------------
        try:
            asg_resp = autoscaling.describe_auto_scaling_instances(InstanceIds=[e.instance_id])
            if asg_resp["AutoScalingInstances"]:
                e.asg_name = asg_resp["AutoScalingInstances"][0]["AutoScalingGroupName"]
        except ClientError:
            pass

        # -------------------------
        # KeyPair (verify existence)
        # -------------------------
        kp = inst.get("KeyName")
        e.keypair = kp if kp and kp in existing_keypairs else None

        # -------------------------
        # EIP
        # -------------------------
        for a in addresses:
            if a.get("InstanceId") == e.instance_id:
                e.eips.append(
                    {
                        "id": a["AllocationId"],
                        "ip": a["PublicIp"],
                        "association_id": a.get("AssociationId")
                    }
                )

        # -------------------------
        # Security Groups
        # -------------------------
        for sg in inst.get("SecurityGroups", []):
            e.security_groups.append(
                {"id": sg["GroupId"], "name": sg["GroupName"]}
            )

        # -------------------------
        # Volumes (IMPORTANT)
        # -------------------------
        root_device = inst.get("RootDeviceName")

        for mapping in inst.get("BlockDeviceMappings", []):
            if "Ebs" not in mapping:
                continue

            vol_id = mapping["Ebs"]["VolumeId"]
            delete_on_term = mapping["Ebs"].get("DeleteOnTermination", False)
            is_root = mapping.get("DeviceName") == root_device
            device_name = mapping.get("DeviceName")

            e.volumes.append(
                {
                    "id": vol_id,
                    "is_root": is_root,
                    "delete_on_termination": delete_on_term,
                    "device_name": device_name,
                }
            )

        # -------------------------
        # Snapshots (ONLY from those volumes)
        # -------------------------
        for v in e.volumes:
            try:
                snaps = ec2.describe_snapshots(
                    Filters=[
                        {"Name": "volume-id", "Values": [v["id"]]}
                    ],
                    OwnerIds=["self"],
                )["Snapshots"]

                for s in snaps:
                    e.snapshots.append(s["SnapshotId"])
            except Exception:
                pass

        # -------------------------
        # Protection flags
        # -------------------------
        try:
            stop_attr = ec2.describe_instance_attribute(
                InstanceId=e.instance_id,
                Attribute="disableApiStop",
            )
            e.stop_protected = stop_attr["DisableApiStop"]["Value"]
        except Exception:
            e.stop_protected = False

        try:
            term_attr = ec2.describe_instance_attribute(
                InstanceId=e.instance_id,
                Attribute="disableApiTermination",
            )
            e.terminate_protected = term_attr["DisableApiTermination"]["Value"]
        except Exception:
            e.terminate_protected = False

        # -------------------------
        # ENIs
        # -------------------------
        for eni in inst.get("NetworkInterfaces", []):
            e.enis.append(
                {
                    "id": eni["NetworkInterfaceId"],
                    "status": eni["Status"],
                    "primary": eni.get("Attachment", {}).get("DeviceIndex") == 0,
                }
            )
