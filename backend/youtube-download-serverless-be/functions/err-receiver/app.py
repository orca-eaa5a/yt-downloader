import logging

logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    logging.error(event['body']['err'])

    return {
        'statusCode': event['statusCode'],
        'err': event['body']['err']
    }
    pass