import os
import json
import boto3
import hashlib
import logging

logging.getLogger().setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION')
STEPFUNCTION_ARN = os.environ.get('STEPFUNCTION_ARN')

def get_stepfunction_client(region=None):
    return boto3.client('stepfunctions', region_name=REGION)

def get_dynamodb_client(region=None):
    return boto3.client('dynamodb', region_name=region)

def dyn_put_item(dyn_client, table_name, item):
    try:
        item['TableName'] = table_name
        resp = dyn_client.put_item(**item)
    except Exception as e:
        logging.error("dynamodb put_item error with: {}".format(str(e)))
        return None
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        logging.error("dynamodb put_item failed with: {}".format(resp['ResponseMetadata']['HTTPStatusCode']))
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