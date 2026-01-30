from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
import boto3
import time

console = Console()

def prompt_tag():
    key = Prompt.ask("Enter Tag Key").strip()
    val = Prompt.ask("Enter Tag Value").strip()
    return key, val

def select_action():
    console.print("\n[bold cyan]Select action:[/bold cyan]")
    console.print("1) Start")
    console.print("2) Stop")
    console.print("3) Terminate")
    choice = Prompt.ask("Enter choice").strip()
    return {"1": "start", "2": "stop", "3": "terminate"}.get(choice)

def confirm():
    return Confirm.ask("Apply changes?")

def show_discovery(ec2s, asgs=None, asg_managed_ec2s=None):
    if not ec2s and not asgs and not asg_managed_ec2s:
        console.print("❌ [red]No resources found with given tag.[/red]")
        return

    for e in ec2s:
        # Panel for EC2
        ec2_info = f"[bold cyan]EC2 Instance:[/bold cyan] {e.instance_id} ({e.name})\n"
        ec2_info += f"[green]State:[/green] {e.state} | [blue]Region:[/blue] {e.region}"
        console.print(Panel(ec2_info, title="[bold]EC2 Resource[/bold]", border_style="blue"))

        # Resources table
        table = Table(title="[bold green]Associated Resources[/bold green]")
        table.add_column("TYPE", style="cyan", no_wrap=True)
        table.add_column("RESOURCE_ID", style="magenta")
        table.add_column("NAME", style="green")
        table.add_column("STATE", style="yellow")

        ec2 = boto3.client("ec2", region_name=e.region)

        # EIP
        for eip in e.eips:
            table.add_row("EIP", eip['id'], eip['ip'], "attached")

        # Security Groups
        for sg in e.security_groups:
            try:
                enis = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg['id']]}])['NetworkInterfaces']
                state = "in-use" if enis else "available"
                table.add_row("SG", sg["id"], sg["name"], state)
            except Exception:
                table.add_row("SG", sg["id"], sg["name"], "unknown")

        # KeyPair
        if e.keypair:
            try:
                instances = ec2.describe_instances(
                    Filters=[
                        {'Name': 'key-name', 'Values': [e.keypair]},
                        {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                    ]
                )['Reservations']
                state = "in-use" if instances else "available"
                table.add_row("KeyPair", e.keypair, e.keypair, state)
            except Exception:
                table.add_row("KeyPair", e.keypair, e.keypair, "unknown")

        # Volumes
        for v in e.volumes:
            try:
                vol = ec2.describe_volumes(VolumeIds=[v["id"]])["Volumes"][0]
                table.add_row("Volume", v["id"], "root" if v["is_root"] else v.get("device_name", "data"), vol["State"])
            except Exception:
                pass

        # Snapshots
        for snap in e.snapshots:
            table.add_row("Snapshot", snap, "", "exists")

        if table.rows:
            console.print(table)
        else:
            console.print("[dim]No associated resources.[/dim]")

        console.print()  # Space between instances

    # ASGs with their managed EC2s
    for asg in asgs:
        asg_info = f"[bold blue]ASG:[/bold blue] {asg.name}\n"
        asg_info += f"[green]Desired:[/green] {asg.desired_capacity} | [blue]Min:[/blue] {asg.min_size} | [red]Max:[/red] {asg.max_size} | [yellow]Region:[/yellow] {asg.region}"
        console.print(Panel(asg_info, title="[bold]Auto Scaling Group[/bold]", border_style="blue"))

        # Show managed EC2s under this ASG
        managed_ec2s = [e for e in (asg_managed_ec2s or []) if e.asg_name == asg.name]
        if managed_ec2s:
            console.print("[bold cyan]Managed EC2 Instances:[/bold cyan]")
            for e in managed_ec2s:
                ec2_info = f"  {e.instance_id} ({e.name}) - {e.state}"
                console.print(f"[dim]{ec2_info}[/dim]")

                # Resources table for managed EC2
                table = Table(title=f"[bold green]Resources for {e.name}[/bold green]")
                table.add_column("TYPE", style="cyan", no_wrap=True)
                table.add_column("RESOURCE_ID", style="magenta")
                table.add_column("NAME", style="green")
                table.add_column("STATE", style="yellow")

                ec2_client = boto3.client("ec2", region_name=e.region)

                # EIP
                for eip in e.eips:
                    table.add_row("EIP", eip['id'], eip['ip'], "attached")

                # Security Groups
                for sg in e.security_groups:
                    try:
                        enis = ec2_client.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg['id']]}])['NetworkInterfaces']
                        state = "in-use" if enis else "available"
                        table.add_row("SG", sg["id"], sg["name"], state)
                    except Exception:
                        table.add_row("SG", sg["id"], sg["name"], "unknown")

                # KeyPair
                if e.keypair:
                    try:
                        instances = ec2_client.describe_instances(
                            Filters=[
                                {'Name': 'key-name', 'Values': [e.keypair]},
                                {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                            ]
                        )['Reservations']
                        state = "in-use" if instances else "available"
                        table.add_row("KeyPair", e.keypair, e.keypair, state)
                    except Exception:
                        table.add_row("KeyPair", e.keypair, e.keypair, "unknown")

                # Volumes
                for v in e.volumes:
                    try:
                        vol = ec2_client.describe_volumes(VolumeIds=[v["id"]])["Volumes"][0]
                        table.add_row("Volume", v["id"], "root" if v["is_root"] else v.get("device_name", "data"), vol["State"])
                    except Exception:
                        pass

                # Snapshots
                for snap in e.snapshots:
                    table.add_row("Snapshot", snap, "", "exists")

                if table.rows:
                    console.print(table)
        else:
            console.print("[dim]No managed EC2 instances.[/dim]")

        console.print()

def show_plan(lines):
    console.print("\n[bold yellow]📋 PLAN:[/bold yellow]")
    console.print("[dim]" + "-" * 80 + "[/dim]")
    for l in lines:
        console.print(l)
