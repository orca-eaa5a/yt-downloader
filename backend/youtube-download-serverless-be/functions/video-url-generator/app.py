import json
import logging

logging.getLogger().setLevel(logging.INFO)

CLOUDFRONT_DOMAIN = "d2h9qmde94lnl.cloudfront.net"
def parameter_validation(event):
    required_params = ['s3_key']
    if 'body' not in event:
        return False
    for p in required_params:
        if not p in event['body']['data']:
            return False
    return True

def lambda_handler(event, context):
    resp = {
        'statusCode': 400,
        'body':{
            'success': False,
            'data': None
        }
    }
    if not parameter_validation(event):
        logging.error("invalid parameter: {}".format(json.dumps(event)))
        resp['body']['err'] = "invalid parameter"
        return resp
    
    resp['body']['data'] = {
        'url': "{}/{}".format(CLOUDFRONT_DOMAIN, event['body']['data']['s3_key'])
    }
    resp['statusCode'] = 200
    resp['body']['success'] = True
    
    return resp