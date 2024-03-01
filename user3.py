import boto3
from datetime import datetime, timezone

def get_access_key_age(access_key_create_date):
    current_time = datetime.now(timezone.utc)
    age = current_time - access_key_create_date
    return age.days

def list_users_with_old_access_keys():
    iam_client = boto3.client('iam')
    users = iam_client.list_users()['Users']

    old_access_keys_users = []

    for user in users:
        user_name = user['UserName']
        access_keys = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']

        for access_key in access_keys:
            access_key_id = access_key['AccessKeyId']
            access_key_create_date = access_key['CreateDate']
            access_key_age = get_access_key_age(access_key_create_date)
            access_key_status = access_key['Status']

            if access_key_age > 3:
                old_access_keys_users.append({
                    'UserName': user_name,
                    'AccessKeyId': access_key_id,
                    'AgeDays': access_key_age,
                    'Status': access_key_status
                })

    if old_access_keys_users:
        print("IAM users with access keys older than 3 days:")
        for user_info in old_access_keys_users:
            print(f"IAM User: {user_info['UserName']}")
            print(f"Access Key ID: {user_info['AccessKeyId']}")
            print(f"Age (days): {user_info['AgeDays']}")
            print(f"Status: {user_info['Status']}")
            print()

def create_access_key(user_name):
    iam_client = boto3.client('iam')
    response = iam_client.create_access_key(UserName=user_name)
    access_key = response['AccessKey']
    print("New access key created successfully:")
    print(f"Access Key ID: {access_key['AccessKeyId']}")
    print(f"Secret Access Key: {access_key['SecretAccessKey']}")

def create_new_user(user_name):
    iam_client = boto3.client('iam')
    iam_client.create_user(UserName=user_name)
    print(f"IAM User '{user_name}' created successfully.")

    create_access_key(user_name)

def delete_old_access_key(user_name):
    iam_client = boto3.client('iam')
    access_keys = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']

    for access_key in access_keys:
        access_key_id = access_key['AccessKeyId']
        access_key_create_date = access_key['CreateDate']
        access_key_age = get_access_key_age(access_key_create_date)
        if access_key_age > 3:
            iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
            print(f"Access key '{access_key_id}' for IAM user '{user_name}' deleted successfully.")

def delete_iam_user(user_name):
    iam_client = boto3.client('iam')
    iam_client = boto3.client('iam')
    access_keys = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']

    for access_key in access_keys:
        access_key_id = access_key['AccessKeyId']
    iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)

    print(f"Access key '{access_key_id}' for IAM user '{user_name}' deleted successfully.")

   # Detach policies
    attached_policies = iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    for policy in attached_policies:
        policy_arn = policy['PolicyArn']
        iam_client.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        print(f"Policy '{policy_arn}' detached from IAM user '{user_name}'")

    # Delete user
    iam_client.delete_user(UserName=user_name)
    print(f"IAM User '{user_name}' deleted successfully.")

def main():
    list_users_with_old_access_keys()

    print("Select an option:")
    print("1. Create a new IAM user with a new access key")
    print("2. Create a new access key for an existing IAM user")
    print("3. Delete old access keys for an IAM user")
    print("4. Delete an IAM user")

    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        new_user_name = input("Enter the new IAM username: ")
        create_new_user(new_user_name)
    elif choice == "2":
        user_name = input("Enter the IAM username to add a new access key: ")
        create_access_key(user_name)
    elif choice == "3":
        user_name = input("Enter the IAM username to delete old access keys: ")
        delete_old_access_key(user_name)
    elif choice == "4":
        user_name = input("Enter the IAM username to delete: ")
        delete_iam_user(user_name)
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
