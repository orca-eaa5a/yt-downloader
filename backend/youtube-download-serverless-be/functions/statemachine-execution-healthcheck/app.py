import os
import logging
from awsutils.aws_util import *

logging.getLogger().setLevel(logging.INFO)

# TrimResultSavedDynamoDB
# StepfunctionJobSavedDynamoDB
TRIM_RESULT_SAVED_TABLE = os.environ.get('TRIM_RESULT_SAVED_TABLE')
STEPFUNCTION_JOB_SAVED_TABLE = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE')

TRIM_RESULT_SAVED_TABLE_PARTITION_KEY = os.environ.get('TRIM_RESULT_SAVED_TABLE_PARTITION_KEY')
TRIM_RESULT_SAVED_TABLE_SORT_KEY = os.environ.get('TRIM_RESULT_SAVED_TABLE_SORT_KEY')

STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY')

TRIM_RESULT_SAVED_TABLE_GSI = os.environ.get('TRIM_RESULT_SAVED_TABLE_GSI')

CLOUDFRONT_DOMAIN = "d2h9qmde94lnl.cloudfront.net"

def parameter_validation(event):
    required_params = ['ticket']
    if 'body' not in event:
        return False
    for p in required_params:
        if not p in event['body']:
            return False
    return True

def parameter_validation(params):
    required_params = ['o_url', 'url', 'sp', 'ep', 'm_duration']
    for p in required_params:
        if not p in params:
            return False
    return True

def lambda_handler(event, context):
    resp = {
        'statusCode': 400,
        'body':{
            'success': False,
            'data': None,
        }
    }
    if not parameter_validation(event):
        logging.error("invalid parameter: {}".format(json.dumps(event)))
        resp['body']['err'] = "invalid parameter"
        return resp
    
    ticket = event['body']['ticket']

    dyn_client = get_dynamodb_client()
    query_result = dyn_get_item(
        dyn_client=dyn_client,
        table_name=STEPFUNCTION_JOB_SAVED_TABLE,
        key={
            STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY: {
                "S": ticket
            }
        })

    if not query_result:
        resp['body']['err'] = "there is no requested stepfunction execution"
        return resp

    exec_arn = query_result['Item']['ExecutionArn']
    sfn_client = get_stepfunction_client()
    check_result = healthcheck_statemachine_execution(sfn_client, exec_arn)
    if not check_result:
        resp['body']['err'] = "fail to health check stepfunction execution"
        return resp
    
    status = check_result['status']

    if status == 'RUNNING':
        resp['statusCode'] = 200
        resp['body']['success'] = True
        resp['body']['data'] = {
            'status': check_result['status']
        }
        pass
    elif status == 'SUCCEEDED':
        trackID = query_result['Item']['UniqueTrackID']
        query_result = dyn_query(
            dyn_client=dyn_client,
            table_name=TRIM_RESULT_SAVED_TABLE,
            index=TRIM_RESULT_SAVED_TABLE_GSI,
            condition_exp={
                'KeyConditionExpression': "UniqueTrackID = :UniqueTrackID",
                'ExpressionAttributeValues':{
                    ':UniqueTrackID': {
                        'S': trackID
                    }
                }
            }
        )
        if not query_result:
            resp['body']['err'] = "dynamodb query failed"
            return resp
        
        if not 'Items' in query_result:
            resp['body']['err'] = "{} is empty".format(TRIM_RESULT_SAVED_TABLE)
            return resp
        
        items = query_result['Items']
        if len(items) > 1:
            logging.error("UniqueTrackID of {} is not unique: {}".format(TRIM_RESULT_SAVED_TABLE, trackID))
            resp['body']['err'] = "requested track is not invalid: {}".format(trackID)
            return resp
        
        if dyn_delete_item(dyn_client, STEPFUNCTION_JOB_SAVED_TABLE, key={
            STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY: {
                "S": ticket
            }
        }):
            resp['body']['err'] = "fail to clear ticket: {}".format(ticket)
            return resp

        track_item = items[0]
        s3_key = track_item['S3Key']['S']
        # bucket = track_item['BucketName']['S']

        resp['body']['data'] = {
            'status': status,
            'url': "{}/{}".format(CLOUDFRONT_DOMAIN, s3_key)
        }

    else:
        logging.info('stepfunction execution does not complete the job with input: {} / output: {}'.format(
            check_result['input'],
            check_result['output'],
        ))
        resp['statusCode'] = 200
        resp['body']['err'] = resp['output']

    return resp

if __name__ =='__main__':
    lambda_handler(event={
        'ticket': ""
    }, context=None)
