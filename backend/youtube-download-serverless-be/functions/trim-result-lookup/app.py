import re
import json
import logging
from awsutils.aws_util import *

YOUTUBE_VIDEO_PREFIX = "https://youtube.com/watch?v="

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
        

def get_body_parameters(event, *args):
    params = {}
    if 'body' in event:
        try:
            body = json.loads(event['body'])
        except TypeError as te:
            if te.args[0].startswith('the JSON object must be str'):
                body = event['body']
            else:
                raise te
        for arg in args:
            if arg in body:
                params[arg] = body[arg]
    
    if not params:
        return None
    
    return params

def lambda_handler(event, context):
    # check requested video is already existed
    # check dynamodb
    params = get_body_parameters(event, 'o_url', 'url', 'sp', 'ep')
    resp = {
        'statusCode': 400,
        'body':{
            'exist': False,
            'data': None
        }
    }
    if not params:
        return resp
    
    video_id:str = params['o_url']
    if video_id.startswith("https"):
        # requested with youtube video url
        regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
        video_id = regex.search(params['o_url']).group(1)
    else:
        # requested with youtube video id
        params['o_url'] = YOUTUBE_VIDEO_PREFIX + video_id
    
    track_range = "{}-{}".format(
        normalize_timestr(params['sp']), normalize_timestr(params['ep'])
    )
    dyn_client = get_dynamodb_client()
    query_result = dyn_get_item(
                dyn_client,
                key=video_id,
                sortkey=track_range
            )
    
    if 'Item' not in query_result:
        resp['statusCode'] = 200
        resp['body']['data'] = params
        logging.error("dynamodb query failed : key={} sortkey={}".format(video_id, track_range))

    else:
        resp['statusCode'] = 200
        resp['body']['exist'] = True
        resp['body']['data'] = {
            "s3_key": query_result['Item']['S3Key']['S'],
            "bucket": query_result['Item']['BucketName']['S'],
            "o_url": params['o_url'],
            "url": params['url'],
        }
    
    return resp

if __name__ == '__main__':
    lambda_handler(event={
        "body": {
            "o_url": "https://www.youtube.com/watch?v=H4bhRn2c8Cc",
            "sp": "00:15:12",
            "ep": "00:20:40"
        }
    }, context=None)