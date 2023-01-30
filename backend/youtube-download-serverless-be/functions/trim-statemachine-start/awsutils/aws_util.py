import os
import json
import boto3
import hashlib
import logging

logging.getLogger().setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION')
STEPFUNCTION_ARN = os.environ.get('STEPFUNCTION_ARN')

def get_stepfunction_client(region=None):
    if not region:
        region = REGION
    return boto3.client('stepfunctions', region_name=REGION)

def get_dynamodb_client(region=None):
    if not region:
        region = REGION
    return boto3.client('dynamodb', region_name=region)

def dyn_put_item(dyn_client, key, exec_arn):
    try:
        resp = dyn_client.put_item(
            TableName=DYN_TABLE_NAME,
            Item={
                DYN_TABLE_PARTIOTN_KEY: {
                    'S': key
                },
                DYN_TABLE_SORT_KEY: {
                    'S': sort_key
                },
                'BucketName': {
                    'S': bucket_name
                },
                'S3Key': {
                    'S': s3_key
                }
            }
        )
    except Exception as e:
        return None
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        return None

    return resp

def launch_stepfunction(sfn_client, input, sync=True):
    try:
        resp = sfn_client.start_execution(
            stateMachineArn=STEPFUNCTION_ARN,
            input=json.dumps(input)
        )
    except Exception as e:
        logging.error("start_execution got error with {}".format(str(e)))
    if 'executionArn' in resp:
        # success to execute stepfunction
        execution_arn = resp['executionArn']
    else:
        return None, None
    return execution_arn, hashlib.sha256(execution_arn.encode()).hexdigest()