import re
import json
import logging
from awsutils.aws_util import *

logging.getLogger().setLevel(logging.INFO)

STEPFUNCTION_JOB_SAVED_TABLE = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE')
STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY = os.environ.get('STEPFUNCTION_JOB_SAVED_TABLE_PARTITION_KEY')
TRACKINFO_SAVED_TABLE_GSI = os.environ.get('TRACKINFO_SAVED_TABLE_GSI')

def parameter_validation(event):
    required_params = ['o_url', 'url', 'sp', 'ep', 'm_duration']
    if 'body' not in event:
        return False
    for p in required_params:
        if not p in event['body']:
            return False
    return True

def generate_unique_trackid(url, sp, ep):
    def normalize_timestr(time_str):
        timestamp = 0
        try:
            time_arr = [int(f) for f in time_str.split(":")]
        except ValueError as ve:
            return None
        time_arr.reverse()
        for n, t in enumerate(time_arr):
            timestamp += pow(60, n)*t
        
        return timestamp
    def extract_videoid(_url):
        regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
        video_id = regex.search(_url).group(1)

    video_id = extract_videoid(url)
    ep = normalize_timestr(ep)
    sp = normalize_timestr(sp)
    track_time = "{}-{}".format(sp, ep)

    return hashlib.sha256("{}:{}".format(video_id, track_time).encode()).hexdigest()



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
    
    track_id = generate_unique_trackid(event['body']['o_url'], event['body']['sp'], event['body']['ep'])
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
                },
                TRACKINFO_SAVED_TABLE_GSI: {
                    'S': track_id
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