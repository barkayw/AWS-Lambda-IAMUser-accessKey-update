import boto3
import datetime
import dateutil.tz
import json
import ast
import time
import sys

BUILD_VERSION = "2.0"
# AWS_REGION = '@@deploymentregion'
# AWS_EMAIL_REGION = '@@emailregion'
SERVICE_ACCOUNT_NAME = 'NOC'
EMAIL_TO_ADMIN = 'barkayw@traiana.com'
EMAIL_FROM = 'barkayw@traiana.com'
### EMAIL_SEND_COMPLETION_REPORT = ast.literal_eval('@@emailsendcompletionreport')
GROUP_LIST = "DoNotDeactivate"

###Length of mask over the IAM Access Key
MASK_ACCESS_KEY_LENGTH = ast.literal_eval('16')

### First email warning
FIRST_WARNING_NUM_DAYS = 70
FIRST_WARNING_MESSAGE = '@@first_warning_message'
### Last email warning
LAST_WARNING_NUM_DAYS = 90
LAST_WARNING_MESSAGE = '@@last_warning_message'

### Max AGE days of key after which it is considered EXPIRED (deactivated)
KEY_MAX_AGE_IN_DAYS = 1809
KEY_EXPIRED_MESSAGE = '@@key_expired_message'

KEY_YOUNG_MESSAGE = '@@key_young_message'

#### ==========================================================

# Character length of an IAM Access Key
ACCESS_KEY_LENGTH = 20
# KEY_STATE_ACTIVE = "Active"
KEY_STATE_INACTIVE = "Inactive"

### ==========================================================

### check to see if the MASK_ACCESS_KEY_LENGTH has been misconfigured
if MASK_ACCESS_KEY_LENGTH > ACCESS_KEY_LENGTH:
    MASK_ACCESS_KEY_LENGTH = 16


### ==========================================================
def tzutc():
    return dateutil.tz.tzutc()


def key_age(username, key_created_date):
    client = boto3.client('iam')
    res = client.list_access_keys(UserName=username)
    ### Use for loop if you are going to run this on production. I just wrote it real quick
    accesskeydate = res['AccessKeyMetadata'][0]['CreateDate']
    accesskeydate = accesskeydate.strftime("%Y-%m-%d %H:%M:%S")
    currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    accesskeyd = time.mktime(datetime.datetime.strptime(accesskeydate, "%Y-%m-%d %H:%M:%S").timetuple())
    currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())

    ### We get the data in seconds. converting it to days
    active_days = (currentd - accesskeyd) / 60 / 60 / 24  ### We get the data in seconds. converting it to days

    return int(round(active_days))


####################################################################################

def lambda_handler(event, context):
    print('*****************************')
    print("RotateAccessKey {0} starting ...".format(BUILD_VERSION))
    print('*****************************')

    ### Connect to AWS APIs
    client = boto3.client('iam')

    users = {}
    data = client.list_users()
    print(data)

    userindex = 0

    for user in data['Users']:
        userid = user['UserId']
        username = user['UserName']
        users[userid] = username

    users_report1 = []
    users_report2 = []

    for user in users:
        userindex += 1
        user_keys = []
        skip = False

        print("---------------------\n"),
        print('userindex {0} '.format(userindex))
        username = users[user]
        print('username: {0} '.format(username))

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
            access_key_id = access_key['AccessKeyId']
            masked_access_key_id = access_key_id
            print ('AccessKeyId {0}'.format(masked_access_key_id))

            existing_key_status = access_key['Status']
            if existing_key_status == 'Inactive':
                key_state = "key is already in an INACTIVE state"
                print(key_state)
                # key_info = {'accesskeyid': masked_access_key_id, 'age': age, 'state': key_state, 'changed': False}
                # user_keys.append(key_info)
                continue
            print('user status: {0}'.format(existing_key_status))

            key_created_date = access_key['CreateDate']
            print('key_created_date {0}'.format(key_created_date))

            age = key_age(username, key_created_date)
            print('age {0} '.format(age))

            key_state = ""
            key_state_changed = False

            if 0 < age < FIRST_WARNING_NUM_DAYS:
                key_state = KEY_YOUNG_MESSAGE
                print(key_state)
            elif FIRST_WARNING_NUM_DAYS <= age < LAST_WARNING_NUM_DAYS:
                key_state = FIRST_WARNING_MESSAGE
                print(key_state)
            elif LAST_WARNING_NUM_DAYS <= age < KEY_MAX_AGE_IN_DAYS:
                key_state = LAST_WARNING_MESSAGE
                print(key_state)
            else:
                key_state = KEY_EXPIRED_MESSAGE
                print(key_state)

                client.update_access_key(UserName=username, AccessKeyId=access_key_id, Status='Inactive')

                # send_deactivate_email(EMAIL_TO_ADMIN, username, age, masked_access_key_id)
                print ("**************************")
                print ("UPDATE ACCESS KEY and Inactive the User for user : " + username)
                # print ("UPDATE ACCESS KEY and SENDING DEACTIVATE EMAIL for user : " + username)
                print ("**************************")

                key_state_changed = True
                # print("key_state {0} ").format(key_state)

                key_info = {'accesskeyid': masked_access_key_id, 'age': age, 'state': key_state,
                            'changed': key_state_changed}
                user_keys.append(key_info)

                user_info_with_username = {'userid': userindex, 'username': username, 'keys': user_keys}
                user_info_without_username = {'userid': userindex, 'keys': user_keys}

                users_report1.append(user_info_with_username)
                users_report2.append(user_info_without_username)

    # finished = str(datetime.now())

    # deactivated_report1 = {'reportdate': finished, 'users': users_report1}
    deactivated_report1 = {'users': users_report1}
    print("---------------------")
    print('deactivated_report : {0} '.format(deactivated_report1))

    # if EMAIL_SEND_COMPLETION_REPORT:
    #   deactivated_report2 = {'users': users_report2}
    #   deactivated_report2 = {'reportdate': finished, 'users': users_report2}
    #   send_completion_email(EMAIL_TO_ADMIN, finished, deactivated_report2)

    print('*****************************')
    # print("Completed {0}: {1}".format(BUILD_VERSION, finished))
    print("Completed {0}:".format(BUILD_VERSION))
    print('*****************************')

    # return deactivated_report1
    return
