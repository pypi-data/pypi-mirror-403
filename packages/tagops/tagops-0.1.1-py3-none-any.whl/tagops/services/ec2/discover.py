import boto3
from ...core.resource import EC2Resource

def discover(context, region):
    ec2 = boto3.client("ec2", region_name=region)
    resources = []

    resp = ec2.describe_instances(
        Filters=[
            {"Name": f"tag:{context.tag_key}", "Values": [context.tag_value]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )

    for r in resp["Reservations"]:
        for i in r["Instances"]:
            name = ""
            for t in i.get("Tags", []):
                if t["Key"] == "Name":
                    name = t["Value"]

            resources.append(
                EC2Resource(
                    instance_id=i["InstanceId"],
                    name=name,
                    state=i["State"]["Name"],
                    region=region,
                )
            )

    return resources
