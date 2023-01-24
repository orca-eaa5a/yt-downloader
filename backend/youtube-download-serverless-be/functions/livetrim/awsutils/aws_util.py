import os
import json
import boto3
import hashlib
import requests

SIGNED_URL_TIMEOUT = 600
lambda_temp_directory = '/tmp'
REGION = os.environ.get('AWS_REGION')
BUCKET_NAME = os.environ.get('TrimmedResultBucket')

DYN_TABLE_NAME = os.environ.get('TrimCacheDynDB')
DYN_TABLE_PARTIOTN_KEY = os.environ.get('TrimCacheDynTablePartitionKey')
DYN_TABLE_SORT_KEY = os.environ.get('TrimCacheDynTableSortKey')

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

def get_directory_usage(dir_name):
    size = 0
    for path, dirs, files in os.walk(dir_name):
        for f in files:
            fp = os.path.join(path, f)
            size += os.stat(fp).st_size
    return size

def write_at_lambda_storage(file_name, raw):
    tmp_file_path = os.path.join(lambda_temp_directory, file_name)
    
    with open(tmp_file_path, 'wb') as f:
        f.write(raw)

    return tmp_file_path

def get_s3_client():
    return boto3.client('s3', region_name=REGION)

def get_dest_bucket():
    return BUCKET_NAME

def get_s3_presigned_url(s3_client, bucket, s3_key, timeout=SIGNED_URL_TIMEOUT):
    s3_signed_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': bucket, 'Key': s3_key},
        ExpiresIn=timeout)
    
    return s3_signed_url

def s3_put_object_wrapper(s3_client, bucket, s3_key, body):
    resp = s3_client.put_object(Body=body, Bucket=bucket, Key=s3_key)
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        assert False
        
    return s3_key

def s3_upload_file_wrapper(s3_client, source, bucket, s3_key):
    with open(source, 'rb') as fp:
        resp = s3_client.put_object(Body=fp, Bucket=bucket, Key=s3_key)
    
    # s3_signed_url = get_s3_presigned_url(
    #     s3_client=s3_client,
    #     bucket=bucket,
    #     s3_key=s3_key,
    #     timeout=180
    # )
    return REGION, bucket, s3_key

def get_dynamodb_client(region=None):
    if not region:
        region = REGION
    return boto3.client('dynamodb', region_name=region)

def dyn_put_item(dyn_client, key, sort_key, bucket_name, s3_key):
    try:
        resp = dyn_client.put_item(
            TableName=DYN_TABLE_NAME,
            Item={
                DYN_TABLE_PARTIOTN_KEY: {
                    'S': key
                },
                DYN_TABLE_SORT_KEY: {
                    'S': sort_key
                },
                'BucketName': {
                    'S': bucket_name
                },
                'S3Key': {
                    'S': s3_key
                }
            }
        )
    except Exception as e:
        return None
    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        return None

    return resp

