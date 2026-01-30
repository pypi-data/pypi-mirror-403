import boto3

def enrich(asgs, region):
    autoscaling = boto3.client("autoscaling", region_name=region)

    for asg in asgs:
        # Get tags
        resp = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg.name]
        )
        if resp["AutoScalingGroups"]:
            asg_data = resp["AutoScalingGroups"][0]
            asg.tags = asg_data.get("Tags", [])
            launch_template = asg_data.get("LaunchTemplate")
            if launch_template:
                asg.launch_template_id = launch_template.get("LaunchTemplateId")