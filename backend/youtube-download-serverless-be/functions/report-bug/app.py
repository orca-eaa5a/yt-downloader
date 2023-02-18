import os
import json
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def parameter_validation(event):
    required_params = ['message']
    if not 'body' in event:
        return False
    for p in required_params:
        if not p in event['body']['data']:
            return False
    return True

def lambda_handler(event, context):
    message = ""
    resp = {
        'statusCode': 400,
        'body':{
            'success': False,
            'data': None,
        }
    }
    sns_client = boto3.client('sns')

    if not parameter_validation(event):
        logging.error("invalid parameter: {}".format(json.dumps(event)))
        resp['body']['err'] = "invalid parameter"
        return resp
    
    message = event['body']['data']['message']
    
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message = message
    )
    if not response or ( not 'MessageId' in response ): 
        logging.error("fail to requiest publish topic: {} / {}".format(SNS_TOPIC_ARN, message))
        resp['body']['err'] = "fail to requiest publish topic"
        return resp
    
    logging.info("publish topic success! {} / {}".format(SNS_TOPIC_ARN, response['MessageId']))
    resp['statusCode'] = 200
    resp['body']['success'] = True
    resp['body']['data'] = response['MessageId']

    return resp

if __name__ == '__main__':
    SNS_TOPIC_ARN = "arn:aws:sns:ap-northeast-2:392039937679:BugReportTopic"
    lambda_handler(
        event={
            'body':{
                'data':{
                    'message': "test message"
                }
            }
        },
        context=None
    )
    pass