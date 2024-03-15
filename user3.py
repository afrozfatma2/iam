import boto3
from datetime import datetime, timezone
from tabulate import tabulate

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
                old_access_keys_users.append([
                    user_name,
                    access_key_id,
                    access_key_age,
                    access_key_status
                ])

    if old_access_keys_users:
        print("IAM users with access keys older than 3 days:")
        print(tabulate(old_access_keys_users, headers=["User Name", "Access Key ID", "Age (days)", "Status"], tablefmt="grid"))
    else:
        print("No IAM users with access keys older than 3 days.")

def create_access_key(user_name):
    iam_client = boto3.client('iam')
    try:
        confirmation = input(f"Are you sure you want to create a new access key for IAM user '{user_name}'? (yes/no): ")
        if confirmation.lower() == 'yes':
            response = iam_client.create_access_key(UserName=user_name)
            access_key = response['AccessKey']
            print("\nNew access key created successfully:")
            print(tabulate([[access_key['AccessKeyId'], access_key['SecretAccessKey']]], headers=["Access Key ID", "Secret Access Key"], tablefmt="grid"))
        else:
            print("Access key creation canceled.")
    except iam_client.exceptions.LimitExceededException:
        print(f"Cannot create a new access key for user '{user_name}'. The maximum number of access keys (2) for this user has been reached.")
        return


def create_new_user(user_name):
    iam_client = boto3.client('iam')
    try:
        confirm = input(f"Do you want to create IAM user '{user_name}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation aborted.")
            return
        iam_client.create_user(UserName=user_name)
        print(f"\nIAM User '{user_name}' created successfully.")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"IAM User '{user_name}' already exists. Please try a different username.")
        return

    create_access_key(user_name)

def delete_old_access_key(user_name):
    iam_client = boto3.client('iam')
    access_keys = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']

    if len(access_keys) == 1:
        print("Only one access key exists for this user. Cannot delete the last access key.")
        return

    # Sort access keys by creation date
    access_keys_sorted = sorted(access_keys, key=lambda x: x['CreateDate'])

    oldest_access_key = access_keys_sorted[0]  # Get the oldest access key

    access_key_id_to_delete = oldest_access_key['AccessKeyId']

    confirm = input(f"Do you want to delete the oldest access key '{access_key_id_to_delete}' for user '{user_name}'? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation aborted.")
        return

    print(f"Deleting the oldest access key '{access_key_id_to_delete}' for user '{user_name}'.")
    iam_client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id_to_delete)
    print(f"Access key '{access_key_id_to_delete}' deleted successfully.")


def delete_iam_user(user_name):
    iam_client = boto3.client('iam')
    access_keys = iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']

    for access_key in access_keys:
        access_key_id = access_key['AccessKeyId']
    confirmation = input(f"Are you sure you want to delete IAM User '{user_name}' and its associated access key '{access_key_id}'? (yes/no): ")
    if confirmation.lower() == 'yes':
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
    else:
        print("User deletion canceled.")


def create_multiple_users(usernames):
    iam_client = boto3.client('iam')
    user_table = []
    for username in usernames:
        try:
            confirm = input(f"Do you want to create IAM user '{username}'? (yes/no): ")
            if confirm.lower() != 'yes':
                print(f"Skipping creation of IAM user '{username}'.")
                user_table.append([username, "Skipped"])
                continue
            iam_client.create_user(UserName=username)
            print(f"\nIAM User '{username}' created successfully.")
            user_table.append([username, "Created"])
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"IAM User '{username}' already exists. Skipping.")
            user_table.append([username, "Skipped"])
            continue

        create_access_key(username)

def delete_multiple_users(usernames):
    for username in usernames:
        delete_iam_user(username)

def main():
    list_users_with_old_access_keys()

    print("\nSelect an option:")
    print("1. Create a new IAM user with a new access key")
    print("2. Create a new access key for an existing IAM user")
    print("3. Delete old access keys for an IAM user")
    print("4. Delete an IAM user")
    print("5. Create multiple IAM users with new access keys")
    print("6. Delete multiple IAM users")

    choice = input("Enter your choice (1/2/3/4/5/6): ")

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
    elif choice == "5":
        user_names = input("Enter the IAM usernames separated by commas: ").split(',')
        create_multiple_users(user_names)
    elif choice == "6":
        user_names = input("Enter the IAM usernames separated by commas: ").split(',')
        delete_multiple_users(user_names)
    else:
        print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

if __name__ == "__main__":
    main()
    
