
import json
import logging
from awsutils.aws_util import *

logging.getLogger().setLevel(logging.INFO)

STEPFUNCTION_JOB_SAVED_TABLE = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE')
STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY')

def parameter_validation(event):
    required_params = ['o_url', 'url', 'sp', 'ep', 'm_duration']
    if 'body' not in event:
        return False
    for p in required_params:
        if not p in event['body']:
            return False
    return True

def lambda_handler(event, context):
    """
    1. start stepfunction
    2. save execution arn to DynamoDB
    3. return sha256(execution arn)
    """
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

    sfn_client = get_stepfunction_client()
    exec_arn, sha = launch_stepfunction(sfn_client, event['body'])
    if not exec_arn:
        logging.error("fail to launch stepfunction statemachine")
        resp['body']['err'] = "stepfunction launch failed"
        return resp
    
    dyn_client = get_dynamodb_client()
    dyn_resp = dyn_put_item(
        dyn_client=dyn_client,
        table_name=STEPFUNCTION_JOB_SAVED_TABLE,
        item={
            'Item':{
                STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY: {
                    'S': sha
                },
                'ExecutionArn':{
                    'S': exec_arn
                }
            }
        })
    
    if not dyn_resp:
        resp['body']['err'] = "fail to save data at dynamodb"
    else:
        resp['body']['success'] = True
        resp['body']['data'] = {
            'ticket': sha
        }
    
    return resp