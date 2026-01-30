import boto3
from botocore.exceptions import ClientError


def get_session():
    return boto3.Session()


def get_account_details(session):
    sts = session.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    account_name = ''

    # First, try to get the account name from AWS Organizations
    try:
        org_client = session.client("organizations")
        response = org_client.describe_account(AccountId=account_id)
        account_name = response.get('Account', {}).get('Name', '')
        if account_name:
            return account_id, account_name
    except ClientError as e:
        # This exception is expected if the account is not part of an organization
        if e.response['Error']['Code'] != 'AWSOrganizationsNotInUseException':
            # Log or handle other potential client errors if necessary
            pass
    except Exception:
        # Handle other exceptions (e.g., credentials not configured for Organizations)
        pass

    # If organization name not found, fall back to IAM alias
    try:
        iam = session.client("iam")
        aliases = iam.list_account_aliases().get('AccountAliases', [])
        if aliases:
            account_name = aliases[0]
    except Exception:
        # This can fail due to permissions, so we pass silently
        pass
        
    return account_id, account_name


def get_all_regions(session):
    ec2 = session.client("ec2", region_name="us-east-1")
    resp = ec2.describe_regions(AllRegions=False)
    return [r["RegionName"] for r in resp["Regions"]]
