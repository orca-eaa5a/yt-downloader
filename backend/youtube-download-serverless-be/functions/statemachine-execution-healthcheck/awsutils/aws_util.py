import os
import json
import boto3
import hashlib
import logging

logging.getLogger().setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION')


def get_stepfunction_client(region=None):
    if not region:
        region = REGION
    return boto3.client('stepfunctions', region_name=REGION)

def get_dynamodb_client(region=None):
    if not region:
        region = REGION
    return boto3.client('dynamodb', region_name=region)

def dyn_get_item(dyn_client, table_name, key):
    query_result = dyn_client.get_item(
        TableName=table_name,
        Key=key
    )
    
    if 'Item' not in query_result:
        logging.error("dynamodb query: no item exists : key={}".format(key))
        return None    
    
    return query_result

def dyn_query(dyn_client, table_name, index, condition_exp):
    condition_exp['TableName'] = table_name
    condition_exp['IndexName'] = index
    try:
        query_result = dyn_client.query(**condition_exp)
    except Exception as e:
        logging.error("dynamodb query failed with {}".format(str(e)))
        return None
        
    return query_result

def dyn_delete_item(dyn_client, table_name, key):
    try:
        dyn_client.delete_item(
            TableName=table_name,
            Key=key
        )
    except Exception as e:
        logging.error("Couldn't delete item {}: {}: {}",
                e.response['Error']['Code'], e.response['Error']['Message'])
        return False
    return True

def healthcheck_statemachine_execution(sfn_client, exec_arn):
    """
    This API action is not supported by EXPRESS state machine executions unless they were dispatched by a Map Run.
    """
    try:
        resp = sfn_client.describe_execution(executionArn=exec_arn)
    except Exception as e:
        logging.error("healthcheck_statemachine_execution got error with {}".format(str(e)))
        return None
        
    if 'status' in resp:
        return resp
    return None