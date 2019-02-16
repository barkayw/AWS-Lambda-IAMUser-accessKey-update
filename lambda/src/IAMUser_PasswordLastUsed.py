import boto3
import datetime
from dateutil.tz import tzutc
import time

# import dateutil.tz
# import json
# import ast
# import sys


BUILD_VERSION = "1.0"
GROUP_LIST = "DoNotDeactivate"
final_report = ''
today = datetime.datetime.now()


def tzutc():
    return dateutil.tz.tzutc()


# def passwordlastused(accesskey):
#         client = boto3.client('iam')
#         res = client.get_access_key_last_used(AccessKeyId=accesskey)
#         accesskeydate = res['AccessKeyLastUsed']['LastUsedDate']
#         accesskeydate = accesskeydate.strftime("%Y-%m-%d %H:%M:%S")
#         currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
#         accesskeyd = time.mktime(datetime.datetime.strptime(accesskeydate, "%Y-%m-%d %H:%M:%S").timetuple())
#         currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
#         active_days = (currentd - accesskeyd)/60/60/24 ### We get the data in seconds. converting it to days

# return int(round(active_days))


####################################################################################

def lambda_handler(event, context):
    print('*****************************')
    print("RotateAccessKey {0} starting ...".format(BUILD_VERSION))
    print('*****************************')

    client = boto3.client('iam')
    users = {}
    userindex = 0

    today = datetime.datetime.now()

    data = client.list_users()
    print(data)
    print('*****************************')

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    for user in users:
        userindex += 1
        user_keys = []
        skip = False
        print("---------------------\n"),
        print('userindex {0} '.format(userindex))
        username = users[user]
        print('User name: {0} '.format(username))

        # key_state = existing_key_status(username)
        # def existing_key_status(username)
        access_keys = client.list_access_keys(UserName=username)
        for access_key in access_keys['AccessKeyMetadata']:
            existing_key_status = access_key['Status']
            print('user status: {0}'.format(existing_key_status))
            if existing_key_status == 'Inactive':
                key_state = "key is already in an INACTIVE state"
                print(key_state)
                skip = True
                break

        if skip:
            continue

        access_keys = client.list_access_keys(UserName=username)
        #       print(access_keys)
        for access_key in access_keys['AccessKeyMetadata']:
            accesskey = access_key['AccessKeyId']
            masked_access_key_id = accesskey
            print('Access key: {0}'.format(masked_access_key_id))

        keys_response = client.list_access_keys(UserName=username)
        last_access = None

        for key in keys_response['AccessKeyMetadata']:
            last_used_response = client.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
            if 'LastUsedDate' in last_used_response['AccessKeyLastUsed']:
                accesskey_last_used = last_used_response['AccessKeyLastUsed']['LastUsedDate']
                accesskey_last_used = accesskey_last_used.strftime("%Y-%m-%d %H:%M:%S")
                if last_access is None or accesskey_last_used < last_access:
                    last_access = accesskey_last_used

        currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        if last_access != None:
            accesskeyd = time.mktime(datetime.datetime.strptime(accesskey_last_used, "%Y-%m-%d %H:%M:%S").timetuple())
            #  print('test:accesskeyd:',accesskeyd)
            currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
            #  print("test:Today: {0}".format(currentdate))
            delta = (currentd - accesskeyd) / 60 / 60 / 24  ### get the data in seconds. converting it to days
            delta = int(delta)
            if delta >= 60:
                print('Accesskey last used: {0}'.format(delta))