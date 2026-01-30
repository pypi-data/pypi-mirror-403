import boto3
from rich.console import Console

console = Console()

def wait_for_termination(ec2s):
    by_region = {}

    for e in ec2s:
        by_region.setdefault(e.region, []).append(e.instance_id)

    for region, ids in by_region.items():
        ec2 = boto3.client("ec2", region_name=region)
        console.print(f"\n[cyan]⏳ Waiting for EC2 termination in {region}...[/cyan]")
        with console.status("", spinner="dots"):
            waiter = ec2.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=ids)
        console.print(f"[green]✅ All EC2 instances terminated in {region}[/green]")
