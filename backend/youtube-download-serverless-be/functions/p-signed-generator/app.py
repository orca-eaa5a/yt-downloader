import json
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

SIGNED_URL_TMOUT = 600

def lambda_handler(event, context):
    """사용자의 요청에 따라 생성한 media를 pre-signed url 생성 후, 사용자에게 응답합니다.

    Parameters
    ----------
    event: dict, required
        Lambda Step Function
    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
    pre-signed url
    """
    """
    body parameter
    s3 key
    """

    resp = {
        'statusCode': 400,
        'body': {
            'success': False,
            'data': None
        }
    }
    
    body = event['body']
    if type(body) == str:
        body = json.loads(body)

    try:
        data = body['data']
        s3_client = boto3.client('s3', region_name=data['bucket_region'])
        s3_signed_url = s3_client.generate_presigned_url('get_object',
            Params={'Bucket': data['bucket'], 'Key': data['s3_key']},
            ExpiresIn=SIGNED_URL_TMOUT)
        resp['statusCode'] = 200
        resp['body']['success'] = True
        resp['body']['data'] = {
            'url': s3_signed_url
        }
        
    except KeyError as e:
        resp['body']['err'] = str(e)
        logging.error("generate_presigned_url error with {}".format(str(e)))
    except Exception as e:
        resp['body']['err'] = str(e)
        logging.error("generate_presigned_url error with {}".format(str(e)))

    return resp
