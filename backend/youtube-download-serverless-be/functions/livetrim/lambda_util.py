import os
import boto3
import hashlib
import requests

SIGNED_URL_TIMEOUT = 600
lambda_temp_directory = '/tmp'

def conver_timestr_to_timestamp(time_str):
    timestamp, _pow = 0, 0
    try:
        time_arr = [float(f) for f in time_str.split(':')]
    except ValueError as ve:
        assert False
    time_arr.reverse()
    for t in time_arr:
        timestamp += pow(60, _pow) * t
        _pow += 1
    del time_arr

    return timestamp

def byterange_request(url, start_byte, end_byte):
    CHUNK_SIZE = 1024*10 # 10mb request
    if end_byte < CHUNK_SIZE:
        CHUNK_SIZE = end_byte

    current_offset = start_byte
    _bin = b''
    if type(start_byte) != int or type(end_byte) != int:
        assert False
    while True:
        end_offset = current_offset + CHUNK_SIZE - 1
        if current_offset + end_offset >= end_byte:
            end_offset = end_byte - 1
        resp = requests.get(url=url, headers={
            'Range': 'bytes={}-{}'.format(current_offset, end_offset)
        })
        if resp.status_code == 206 or resp.status_code == 200:
            current_offset += len(resp.content)
            _bin += resp.content
            if current_offset >= end_byte:
                break
        else:
            assert False
    
    return _bin

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

def create_s3_client_object():
    client = boto3.client('s3')
    return client

def get_dest_bucket():
    bucket = os.environ.get('TrimmedResultBucket')

    return bucket

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
    
    s3_signed_url = get_s3_presigned_url(
        s3_client=s3_client,
        bucket=bucket,
        s3_key=s3_key,
        timeout=180
    )
    return s3_signed_url