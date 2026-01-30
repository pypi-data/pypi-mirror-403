from .core.aws import get_session, get_account_details, get_all_regions
from .core.context import ExecutionContext
from .core.ui import (
    prompt_tag,
    select_action,
    confirm,
    show_discovery,
    show_plan,
)
from .services.ec2.discover import discover
from .services.ec2.enrich import enrich
from .services.ec2 import actions
from .services.asg.discover import discover as asg_discover
from .services.asg.enrich import enrich as asg_enrich
from .services.asg import actions as asg_actions
from rich.console import Console
from rich.progress import Progress

console = Console()

console = Console()


def main():
    console.print("[bold cyan]████████╗  █████╗   ██████╗  ██████╗ ██████╗ ███████╗[/bold cyan]")
    console.print("[bold cyan]╚══██╔══╝ ██╔══██╗ ██╔════╝ ██╔═══██╗██╔══██╗██╔════╝[/bold cyan]")
    console.print("[bold cyan]   ██║    ███████║ ██║  ███╗██║   ██║██████╔╝███████╗[/bold cyan]")
    console.print("[bold cyan]   ██║    ██╔══██║ ██║   ██║██║   ██║██╔═══╝ ╚════██║[/bold cyan]")
    console.print("[bold cyan]   ██║    ██║  ██║ ╚██████╔╝╚██████╔╝██║     ███████║[/bold cyan]")
    console.print("[bold cyan]   ╚═╝    ╚═╝  ╚═╝  ╚═════╝  ╚═════╝ ╚═╝     ╚══════╝[/bold cyan]")
    console.print("[dim]AWS Tag-Based Operations Tool - Safe and Efficient Resource Management[/dim]")
    console.print()

    session = get_session()
    account_id, account_alias = get_account_details(session)
    
    # Format account ID with hyphens
    formatted_account_id = f"{account_id[:4]}-{account_id[4:8]}-{account_id[8:]}"

    console.print("[bold green]Account ID[/bold green]")
    console.print(f"{formatted_account_id}")
    console.print("[bold green]Account name[/bold green]")
    console.print(f"{account_alias if account_alias else 'Not Set'}")
    console.print()

    tag_key, tag_value = prompt_tag()
    context = ExecutionContext(tag_key, tag_value, account_id)

    regions = get_all_regions(session)
    console.print(f"[dim]Found {len(regions)} regions to scan[/dim]")
    all_ec2s = []
    all_asgs = []

    with Progress() as progress:
        task = progress.add_task("[green]🔍 Scanning regions for tagged resources...", total=len(regions))
        for region in regions:
            try:
                ec2s = discover(context, region)
                if ec2s:
                    enrich(ec2s, region)
                    all_ec2s.extend(ec2s)

                asgs = asg_discover(context, region)
                if asgs:
                    asg_enrich(asgs, region)
                    all_asgs.extend(asgs)
            except Exception:
                pass
            progress.update(task, advance=1)

    # Filter out EC2s that are managed by ASGs
    standalone_ec2s = [e for e in all_ec2s if not e.asg_name]
    asg_managed_ec2s = [e for e in all_ec2s if e.asg_name]

    # Filter out EC2s that are managed by ASGs
    standalone_ec2s = [e for e in all_ec2s if not e.asg_name]
    asg_managed_ec2s = [e for e in all_ec2s if e.asg_name]

    show_discovery(standalone_ec2s, all_asgs, asg_managed_ec2s)

    if not all_ec2s and not all_asgs:
        return

    action = select_action()
    if not action:
        console.print("[red]❌ Invalid choice[/red]")
        return

    plan = []

    for e in standalone_ec2s:
        if action == "start":
            if e.state == "stopped":
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] → START"
                )
            else:
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] {e.state} (skip)"
                )

        elif action == "stop":
            if e.state != "running":
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] {e.state} (skip)"
                )
            elif e.stop_protected:
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] 🚫 STOP-PROTECTED (skip)"
                )
            else:
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] → STOP"
                )

        elif action == "terminate":
            if e.state == "terminated":
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] terminated (skip)"
                )
            elif e.stop_protected or e.terminate_protected:
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] 🚫 PROTECTED (skip)"
                )
            else:
                plan.append(
                    f"EC2 {e.instance_id} ({e.name}) [{e.region}] → TERMINATE"
                )

    for asg in all_asgs:
        if action == "start":
            if asg.desired_capacity == 0:
                plan.append(
                    f"ASG {asg.name} [{asg.region}] → START (to desired: {asg.original_desired_capacity}, min: {asg.original_min_size}, max: {asg.original_max_size})"
                )
            else:
                plan.append(
                    f"ASG {asg.name} [{asg.region}] already running (skip)"
                )

        elif action == "stop":
            if asg.desired_capacity > 0:
                plan.append(
                    f"ASG {asg.name} [{asg.region}] → STOP (to desired: 0, min: 0, max: 0)"
                )
            else:
                plan.append(
                    f"ASG {asg.name} [{asg.region}] already stopped (skip)"
                )

        elif action == "terminate":
            plan.append(
                f"ASG {asg.name} [{asg.region}] → TERMINATE"
            )

    show_plan(plan)

    if not confirm():
        console.print("[yellow]Aborted.[/yellow]")
        return

    console.print("\n[bold green]🚀 Executing...[/bold green]\n")

    if action == "start":
        actions.start(standalone_ec2s)
        asg_actions.start(all_asgs)
    elif action == "stop":
        actions.stop(standalone_ec2s)
        asg_actions.stop(all_asgs)
    elif action == "terminate":
        actions.terminate(standalone_ec2s, context, all_ec2s, all_asgs)
        asg_actions.terminate(all_asgs)

    console.print("\n[green]✅ Done.[/green]")


if __name__ == "__main__":
    main()
