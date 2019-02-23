import boto3
import datetime
from dateutil.tz import tzutc
import time
#import dateutil.tz
#import json
#import ast
#import sys


BUILD_VERSION = "1.0"
GROUP_LIST = "DoNotDeactivate"
final_report = ''

today = datetime.datetime.now()
users = {}
userindex = 0

# def tzutc():
#     return dateutil.tz.tzutc()

def existing_key_status(username):
    client = boto3.client('iam')
    access_keys = client.list_access_keys(UserName=username)
    for access_key in access_keys['AccessKeyMetadata']:
            existing_key_status = access_key['Status']
            print('user status: {0}'.format(existing_key_status))
            # if existing_key_status == 'Inactive':
            #         key_state = "key is already in an INACTIVE state"
            #         print(key_state)
            #         skip = True
            #         break

            # if skip:
            #     continue


    return(existing_key_status)

def masked_access_key_id(username):
    client = boto3.client('iam')
    access_keys = client.list_access_keys(UserName=username)
    for access_key in access_keys['AccessKeyMetadata']:
        accesskey = access_key['AccessKeyId']
        masked_access_key_id = accesskey
        print ('Access key: {0}'.format(masked_access_key_id))

    return(masked_access_key_id)

def accesskey_last_used(username):
    client = boto3.client('iam')
    keys_response = client.list_access_keys(UserName=username)
    last_access = None
    for key in keys_response['AccessKeyMetadata']:
        last_used_response = client.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
        if 'LastUsedDate' in last_used_response['AccessKeyLastUsed']:
            accesskey_last_used = last_used_response['AccessKeyLastUsed']['LastUsedDate']
            accesskey_last_used = accesskey_last_used.strftime("%Y-%m-%d %H:%M:%S")
            if last_access is None or accesskey_last_used < last_access:
                last_access = accesskey_last_used

    return(last_access)

def deltalastused(last_access, username, masked_access_key_id):
    currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    if last_access != None:
        accesskeyd = time.mktime(datetime.datetime.strptime(last_access, "%Y-%m-%d %H:%M:%S").timetuple())
        currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
        delta = (currentd - accesskeyd) / 60 / 60 / 24 ### get the data in seconds. converting it to days
        delta = int(delta)
        print('pass days last used: {0}'.format(delta))
        if delta >= 180:
            print('Access Key unused over 180 days deleted')
        elif delta >=90:
            print('Access Key unused over 90 days Change status to Inactive')
            # client.update_access_key(UserName=username, AccessKeyId=masked_access_key_id, Status='Inactive')




####################################################################################

def lambda_handler(event, context):
    users = {}
    userindex = 0
    client = boto3.client('iam')
    today = datetime.datetime.now()
    data = client.list_users()
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
        print("\n---------------------"),
        print('userindex {0} '.format(userindex))
        username = users[user]
        print('User name: {0} '.format(username))

        key_state = existing_key_status(username)

        # if existing_key_status == 'Inactive':
        #         key_state = "key is already in an INACTIVE state"
        #         print(key_state)
        #         skip = True
        #         break

        # if skip:
        #     continue

        user_groups = client.list_groups_for_user(UserName=username)
        for groupName in user_groups['Groups']:
            if groupName['GroupName'] == GROUP_LIST:
                print('Detected that user belongs to exclusion group: {0}'.format(GROUP_LIST)),
                print("\nDo Not invalidate Access Key")
                skip = True
                break

        if skip:
            continue

        access_key =masked_access_key_id(username)

        last_access = accesskey_last_used(username)

        delta = deltalastused(last_access, username, masked_access_key_id)