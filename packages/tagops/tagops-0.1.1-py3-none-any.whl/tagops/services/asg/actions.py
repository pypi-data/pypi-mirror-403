import boto3
from rich.console import Console

console = Console()


def start(asgs):
    for asg in asgs:
        autoscaling = boto3.client("autoscaling", region_name=asg.region)
        ec2 = boto3.client("ec2", region_name=asg.region)
        try:
            # Start ASG by restoring original min, desired, and max
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=asg.name,
                MinSize=asg.original_min_size,
                DesiredCapacity=asg.original_desired_capacity,
                MaxSize=asg.original_max_size
            )
            console.print(f"[green]✅ Started ASG {asg.name} (desired: {asg.original_desired_capacity}, min: {asg.original_min_size}, max: {asg.original_max_size}) [{asg.region}][/green]")
            
            # Remove the stored original value tags
            autoscaling.delete_tags(
                Tags=[
                    {
                        "Key": "TagOps-Original-Min",
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group"
                    },
                    {
                        "Key": "TagOps-Original-Max",
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group"
                    },
                    {
                        "Key": "TagOps-Original-Desired",
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group"
                    }
                ]
            )
        except Exception as err:
            console.print(f"[red]❌ Failed to start ASG {asg.name}: {err}[/red]")


def stop(asgs):
    for asg in asgs:
        autoscaling = boto3.client("autoscaling", region_name=asg.region)
        try:
            # Store original values in tags
            autoscaling.create_or_update_tags(
                Tags=[
                    {
                        "Key": "TagOps-Original-Min",
                        "Value": str(asg.original_min_size),
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group",
                        "PropagateAtLaunch": False
                    },
                    {
                        "Key": "TagOps-Original-Max",
                        "Value": str(asg.original_max_size),
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group",
                        "PropagateAtLaunch": False
                    },
                    {
                        "Key": "TagOps-Original-Desired",
                        "Value": str(asg.original_desired_capacity),
                        "ResourceId": asg.name,
                        "ResourceType": "auto-scaling-group",
                        "PropagateAtLaunch": False
                    }
                ]
            )
            
            # To fully stop ASG, set min, desired, and max to 0
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=asg.name,
                MinSize=0,
                DesiredCapacity=0,
                MaxSize=0
            )
            console.print(f"[green]✅ Stopped ASG {asg.name} (desired: 0, min: 0, max: 0) [{asg.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to stop ASG {asg.name}: {err}[/red]")


def terminate(asgs):
    for asg in asgs:
        autoscaling = boto3.client("autoscaling", region_name=asg.region)
        ec2 = boto3.client("ec2", region_name=asg.region)
        try:
            # Check if any instances in the ASG have termination protection
            resp = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg.name])
            if resp["AutoScalingGroups"]:
                instance_ids = [i["InstanceId"] for i in resp["AutoScalingGroups"][0]["Instances"]]
                if instance_ids:
                    instances_resp = ec2.describe_instances(InstanceIds=instance_ids)
                    for reservation in instances_resp["Reservations"]:
                        for instance in reservation["Instances"]:
                            if instance.get("DisableApiTermination", {}).get("Value", False):
                                console.print(f"[yellow]⚠️ ASG {asg.name} has instances with termination protection – skipping [{asg.region}][/yellow]")
                                continue  # Skip this ASG

            # First scale to 0 by setting min to 0 and desired to 0
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=asg.name,
                MinSize=0,
                DesiredCapacity=0
            )
            console.print(f"[yellow]⚠️ Scaled ASG {asg.name} to 0 [{asg.region}][/yellow]")

            # Wait for scale down (simple wait)
            import time
            time.sleep(10)

            # Delete ASG
            autoscaling.delete_auto_scaling_group(
                AutoScalingGroupName=asg.name,
                ForceDelete=True
            )
            console.print(f"[green]✅ Deleted ASG {asg.name} [{asg.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to terminate ASG {asg.name}: {err}[/red]")