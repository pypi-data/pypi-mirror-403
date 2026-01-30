import boto3
from ...core.resource import ASGResource

def discover(context, region):
    autoscaling = boto3.client("autoscaling", region_name=region)
    resources = []

    resp = autoscaling.describe_auto_scaling_groups(
        Filters=[
            {"Name": f"tag:{context.tag_key}", "Values": [context.tag_value]},
        ]
    )

    for asg in resp["AutoScalingGroups"]:
        # Get full ASG details including tags
        full_resp = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg["AutoScalingGroupName"]])
        if full_resp["AutoScalingGroups"]:
            full_asg = full_resp["AutoScalingGroups"][0]
            tags = {tag["Key"]: tag["Value"] for tag in full_asg.get("Tags", [])}
            original_min = int(tags.get("TagOps-Original-Min", asg["MinSize"]))
            original_max = int(tags.get("TagOps-Original-Max", asg["MaxSize"]))
            original_desired = int(tags.get("TagOps-Original-Desired", asg["DesiredCapacity"]))
        else:
            original_min = asg["MinSize"]
            original_max = asg["MaxSize"]
            original_desired = asg["DesiredCapacity"]

        resources.append(
            ASGResource(
                name=asg["AutoScalingGroupName"],
                region=region,
                min_size=asg["MinSize"],
                max_size=asg["MaxSize"],
                desired_capacity=asg["DesiredCapacity"],
                original_min_size=original_min,
                original_max_size=original_max,
                original_desired_capacity=original_desired,
            )
        )

    return resources