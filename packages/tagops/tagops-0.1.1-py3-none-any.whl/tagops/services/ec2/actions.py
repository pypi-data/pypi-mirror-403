import boto3
import time
from ...utils.waiter import wait_for_termination
from rich.console import Console

console = Console()


def start(ec2s):
    for e in ec2s:
        if e.state != "stopped":
            continue

        ec2 = boto3.client("ec2", region_name=e.region)
        try:
            ec2.start_instances(InstanceIds=[e.instance_id])
            console.print(f"[green]✅ Started EC2 {e.instance_id} ({e.name}) [{e.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to start {e.instance_id}: {err}[/red]")


def stop(ec2s):
    for e in ec2s:
        if e.state != "running":
            continue

        if e.stop_protected:
            console.print(
                f"[yellow]⚠️  EC2 {e.instance_id} ({e.name}) [{e.region}] "
                f"has Stop Protection enabled – skipping[/yellow]"
            )
            continue

        ec2 = boto3.client("ec2", region_name=e.region)
        try:
            ec2.stop_instances(InstanceIds=[e.instance_id])
            console.print(f"[green]✅ Stopped EC2 {e.instance_id} ({e.name}) [{e.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to stop {e.instance_id}: {err}[/red]")


def terminate(ec2s, context, all_ec2s, asgs):
    """
    TERMINATE = cleanup project completely
    """

    ec2s_to_terminate = []
    leftovers = []

    for e in ec2s:
        if e.state == "terminated":
            leftovers.append(e)
        elif e.stop_protected or e.terminate_protected:
            console.print(
                f"[yellow]⚠️  EC2 {e.instance_id} ({e.name}) [{e.region}] "
                f"is protected – skipping termination[/yellow]"
            )
        else:
            ec2s_to_terminate.append(e)

    # -------------------------
    # Phase 1: Terminate EC2s
    # -------------------------
    for e in ec2s_to_terminate:
        ec2 = boto3.client("ec2", region_name=e.region)
        try:
            ec2.terminate_instances(InstanceIds=[e.instance_id])
            console.print(f"[green]✅ Terminated EC2 {e.instance_id} ({e.name}) [{e.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to terminate {e.instance_id}: {err}[/red]")

    if ec2s_to_terminate:
        wait_for_termination(ec2s_to_terminate)
        # Update states in all_ec2s
        for e in ec2s_to_terminate:
            e.state = 'terminated'

    # Phase 2: Cleanup leftovers by resource type
    # ---------------------------------------------
    cleanup_targets = ec2s_to_terminate + leftovers

    if not cleanup_targets:
        console.print("[dim]📭 Nothing to clean up.[/dim]")
        return

    console.print("\n[bold blue]🧹 Cleaning up remaining resources...[/bold blue]")

    # Collect SGs and KeyPairs used by Launch Templates from ALL launch templates in regions with cleanup targets
    regions_to_check = set(e.region for e in cleanup_targets)
    launch_template_resources = {}  # region -> {'sg_ids': set(), 'keypairs': set()}
    
    for region in regions_to_check:
        launch_template_resources[region] = {'sg_ids': set(), 'keypairs': set()}
        try:
            ec2 = boto3.client("ec2", region_name=region)
            paginator = ec2.get_paginator('describe_launch_templates')
            for page in paginator.paginate():
                for template in page["LaunchTemplates"]:
                    lt_id = template['LaunchTemplateId']
                    versions_paginator = ec2.get_paginator('describe_launch_template_versions')
                    for versions_page in versions_paginator.paginate(LaunchTemplateId=lt_id):
                        for version in versions_page['LaunchTemplateVersions']:
                            lt_data = version.get("LaunchTemplateData", {})
                            
                            # Collect SGs from top-level and network interfaces
                            launch_template_resources[region]['sg_ids'].update(lt_data.get("SecurityGroupIds", []))
                            for ni in lt_data.get('NetworkInterfaces', []):
                                launch_template_resources[region]['sg_ids'].update(ni.get('Groups', []))

                            # Collect key pairs
                            key_name = lt_data.get("KeyName")
                            if key_name:
                                launch_template_resources[region]['keypairs'].add(key_name)
        except Exception as e:
            console.print(f"[red]Error collecting launch template resources in {region}: {e}[/red]")

    # 1. Delete ENIs
    console.print("Deleting ENIs...")
    all_enis = []
    for e in cleanup_targets:
        all_enis.extend([{"id": eni["id"], "region": e.region} for eni in e.enis])

    for eni in all_enis:
        try:
            ec2 = boto3.client("ec2", region_name=eni["region"])
            eni_resp = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni["id"]])
            eni_data = eni_resp["NetworkInterfaces"][0]
            attachment = eni_data.get("Attachment")
            if attachment:
                attached_to = attachment.get("InstanceId", "unknown resource")
                console.print(f"[yellow]⚠️ Skipping ENI {eni['id']} - attached to instance {attached_to}[/yellow]")
                continue

            ec2.delete_network_interface(NetworkInterfaceId=eni["id"])
            console.print(f"[green]✅ Deleted ENI {eni['id']} [{eni['region']}][/green]")
        except Exception as err:
            if "NotFound" in str(err):
                pass
            else:
                console.print(f"[red]❌ Failed to delete ENI {eni['id']}: {err}[/red]")

    # 2. Release EIPs
    for e in cleanup_targets:
        ec2 = boto3.client("ec2", region_name=e.region)
        for eip in e.eips:
            try:
                ec2.release_address(AllocationId=eip["id"])
                console.print(f"[green]✅ Released EIP {eip['id']} ({eip['ip']}) [{e.region}][/green]")
            except Exception as err:
                # EIP might already be gone if the ENI it was attached to was deleted, which is fine.
                if "InvalidAllocationID.NotFound" in str(err):
                    pass
                else:
                    console.print(f"[red]❌ Failed to release EIP {eip['id']}: {err}[/red]")
    
    # 3. Delete KeyPairs
    for e in cleanup_targets:
        if not e.keypair:
            continue
        
        ec2 = boto3.client("ec2", region_name=e.region)
        
        # Check if KeyPair is used by Launch Templates
        region_resources = launch_template_resources.get(e.region, {})
        if e.keypair in region_resources.get('keypairs', set()):
            console.print(f"[yellow]⚠️ Skipping KeyPair {e.keypair} - associated with a Launch Template in {e.region}[/yellow]")
            continue

        # Check if KeyPair is used by any other instances
        try:
            instances_resp = ec2.describe_instances(
                Filters=[
                    {'Name': 'key-name', 'Values': [e.keypair]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                ]
            )
            instances_using_key = [
                inst['InstanceId'] for res in instances_resp['Reservations'] for inst in res['Instances']
                if inst['InstanceId'] not in {t.instance_id for t in cleanup_targets}
            ]
            if instances_using_key:
                console.print(f"[yellow]⚠️ Skipping KeyPair {e.keypair} - still in use by instances: {', '.join(instances_using_key)}[/yellow]")
                continue
        except Exception:
            console.print(f"[red]❌ Failed to check KeyPair usage for {e.keypair}. Skipping deletion.[/red]")
            continue

        try:
            ec2.delete_key_pair(KeyName=e.keypair)
            console.print(f"[green]✅ Deleted KeyPair {e.keypair} [{e.region}][/green]")
        except Exception as err:
            console.print(f"[red]❌ Failed to delete KeyPair {e.keypair}: {err}[/red]")

    # 4. Delete Security Groups
    for e in cleanup_targets:
        ec2 = boto3.client("ec2", region_name=e.region)
        for sg in e.security_groups:
            if sg["name"] == "default":
                continue

            region_resources = launch_template_resources.get(e.region, {})
            if sg["id"] in region_resources.get('sg_ids', set()):
                console.print(f"[yellow]⚠️ Skipping SG {sg['id']} ({sg['name']}) - associated with a Launch Template in {e.region}[/yellow]")
                continue
            
            try:
                # Re-check for dependencies right before deletion
                enis = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg['id']]}])['NetworkInterfaces']
                # Filter out ENIs attached to instances that are being terminated
                active_enis = [
                    eni for eni in enis
                    if eni.get('Attachment', {}).get('InstanceId') not in {t.instance_id for t in cleanup_targets}
                ]
                if active_enis:
                    attachments = [f"ENI {eni['NetworkInterfaceId']}" for eni in active_enis]
                    console.print(f"[yellow]⚠️ Skipping SG {sg['id']} ({sg['name']}) - still in use by: {', '.join(attachments)}[/yellow]")
                    continue

                ec2.delete_security_group(GroupId=sg["id"])
                console.print(f"[green]✅ Deleted SecurityGroup {sg['id']} ({sg['name']}) [{e.region}][/green]")
            except Exception as err:
                if 'DependencyViolation' in str(err):
                     console.print(f"[yellow]⚠️ Skipping SG {sg['id']} ({sg['name']}) - it is in use by other resources.[/yellow]")
                else:
                    pass

    # 5. Delete Volumes
    for e in cleanup_targets:
        ec2 = boto3.client("ec2", region_name=e.region)
        for v in e.volumes:
            try:
                vol = ec2.describe_volumes(VolumeIds=[v["id"]])["Volumes"][0]
                if vol["State"] == "available":
                    ec2.delete_volume(VolumeId=v["id"])
                    console.print(f"[green]✅ Deleted Volume {v['id']} [{e.region}][/green]")
                # If 'in-use' on a terminated instance, it might become available. Let's retry.
                elif vol.get('Attachments', [{}])[0].get('InstanceId') in {t.instance_id for t in cleanup_targets}:
                    for attempt in range(10): # Retry for ~50s
                        time.sleep(5)
                        vol_state = ec2.describe_volumes(VolumeIds=[v["id"]])["Volumes"][0]["State"]
                        if vol_state == "available":
                            ec2.delete_volume(VolumeId=v["id"])
                            console.print(f"[green]✅ Deleted Volume {v['id']} [{e.region}][/green]")
                            break
                    else: # if loop finishes without break
                         console.print(f"[yellow]⚠️ Skipping Volume {v['id']} - did not become available after instance termination [{e.region}][/yellow]")
                else:
                    console.print(f"[yellow]⚠️ Skipping Volume {v['id']} ({vol['State']}) - not available for deletion [{e.region}][/yellow]")

            except Exception as err:
                if "InvalidVolume.NotFound" in str(err):
                    console.print(f"[dim]📭 Volume {v['id']} already deleted [{e.region}][/dim]")
                else:
                    console.print(f"[red]❌ Failed to check/delete Volume {v['id']}: {err}[/red]")

    # 6. Delete Snapshots
    for e in cleanup_targets:
        ec2 = boto3.client("ec2", region_name=e.region)
        for snap_id in e.snapshots:
            try:
                ec2.delete_snapshot(SnapshotId=snap_id)
                console.print(f"[green]✅ Deleted Snapshot {snap_id} [{e.region}][/green]")
            except Exception:
                pass
