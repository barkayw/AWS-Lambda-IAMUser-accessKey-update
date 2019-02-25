import boto3
import datetime
from dateutil.tz import tzutc
import time

BUILD_VERSION = "1.0"
GROUP_LIST = "DoNotDeactivate"

today = datetime.datetime.now()
users = {}
userindex = 0

####################################################################################

def lambda_handler(event, context):
    users = {}
    userindex = 0
    client = boto3.client('iam')
    today = datetime.datetime.now()
    data = client.list_users()
    currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print('*****************************')
    print("RotateAccessKey {0} starting ...".format(BUILD_VERSION))
    print('*****************************')

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    for user in users:
        userindex += 1
        user_keys = []
        skip = False
        last_access = None

        print("\n---------------------"),
        print('userindex {0} '.format(userindex))
        username = users[user]
        print('User name: {0} '.format(username))

        user_groups = client.list_groups_for_user(UserName=username)
        for groupName in user_groups['Groups']:
            if groupName['GroupName'] == GROUP_LIST:
                print('Detected that user belongs to exclusion group: {0}'.format(GROUP_LIST)),
                print("\nDo Not invalidate Access Key")
                skip = True
                break

        if skip:
            continue

        access_keys = client.list_access_keys(UserName=username)
        for access_key in access_keys['AccessKeyMetadata']:
            existing_key_status = access_key['Status']
            print('user status: {0}'.format(existing_key_status))
            accesskey = access_key['AccessKeyId']
            print('Access key: {0}'.format(accesskey))
            key_created_date = access_key['CreateDate']

            currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
            keycreateddate = key_created_date.strftime("%Y-%m-%d %H:%M:%S")
            accesskeyd = time.mktime(datetime.datetime.strptime(keycreateddate, "%Y-%m-%d %H:%M:%S").timetuple())
            active_days = (currentd - accesskeyd) / 60 / 60 / 24

            last_used_response = client.get_access_key_last_used(AccessKeyId=access_key['AccessKeyId'])
            if 'LastUsedDate' in last_used_response['AccessKeyLastUsed']:
                accesskey_last_used = last_used_response['AccessKeyLastUsed']['LastUsedDate']
                accesskey_last_used = accesskey_last_used.strftime("%Y-%m-%d %H:%M:%S")
                if last_access is None or accesskey_last_used < last_access:
                    last_access = accesskey_last_used

        #     if existing_key_status == 'Inactive':
        #         print("key is already in an INACTIVE state")
        #         skip = True
        #         break

        # if skip:
        #     continue

        if last_access != None:
            accesskeyd = time.mktime(datetime.datetime.strptime(last_access, "%Y-%m-%d %H:%M:%S").timetuple())
            currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
            delta = (currentd - accesskeyd) / 60 / 60 / 24  ### get the data in seconds. converting it to days
            delta = int(delta)
            print('pass days last used: {0}'.format(delta))
            if delta >= 180:
                print('Unused over 180 days Access Key DELETED')
                client.delete_access_key(UserName=username, AccessKeyId=accesskey)
            elif delta >= 90:
                print('Unused over 90 days Access Key status Change to Inactive')
                client.update_access_key(UserName=username, AccessKeyId=accesskey, Status='Inactive')

        if last_access == None and active_days > 90:
            print('Never used over 90 days')

            list_attached_policies = client.list_attached_user_policies(UserName=username)
            policyarns = list_attached_policies['AttachedPolicies']
            for arn in policyarns:
                policyarn = arn['PolicyArn']
                client.detach_user_policy(UserName=username, PolicyArn=policyarn)

            list_inline_policies = client.list_user_policies(UserName=username)
            policynames = list_inline_policies['PolicyNames']
            for inpolicy in policynames:
                client.delete_user_policy(UserName=username, PolicyName=inpolicy)

            client.delete_user(UserName=username)