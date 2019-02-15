import boto3
import datetime
import dateutil.tz
import json
import ast
import time
import sys

username = 'danielmkops'
accesskey = 'AKIAIXUFZSZPBGABG23Q'


# accesskey = 'AKIAIEFEUQU6PLVQ4NAA'
# accesskey = 'AKIAI4IRC5WCJ3OJ7NYQ'

def accesskey_1(accesskey):
    client = boto3.client('iam')
    res = client.get_access_key_last_used(AccessKeyId=accesskey)
    accesskeydate = res['AccessKeyLastUsed']['LastUsedDate']
    accesskeydate = accesskeydate.strftime("%Y-%m-%d %H:%M:%S")
    currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    accesskeyd = time.mktime(datetime.datetime.strptime(accesskeydate, "%Y-%m-%d %H:%M:%S").timetuple())
    currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
    active_days = (currentd - accesskeyd) / 60 / 60 / 24  ### We get the data in seconds. converting it to days

    return int(round(active_days))


def lambda_handler(event, context):
    print(accesskey_1(accesskey))