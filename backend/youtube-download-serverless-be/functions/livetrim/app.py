import os
import ssl
import shutil
import hashlib
import boto3
import math
import json
import pymp4
from mp4parser import MpegTool
import subprocess
from lambda_util import *

SIGNED_URL_TIMEOUT = 600
tmp_path_s3_key = 'tmp'
result_path_s3_key = 'result'

ssl._create_default_https_context = ssl._create_unverified_context
ffmpeg_bin = '/opt/ffmpeg'

def get_body_parameters(event, *args):
    params = {}
    if 'body' in event:
        body = json.loads(event['body'])
        for arg in args:
            if arg in body:
                params[arg] = body[arg]
    
    if not params:
        return None
    
    return params

def live_trim(url:str, sp:str, ep:str):
    tool = MpegTool()
    chunk_sz = 0
    # at first read its header
    chunk_sz = 100 # only read first 100 byte
    content = byterange_request(url, start_byte=0, end_byte=chunk_sz)
    tool.parser.set_binary(content)
    moov_sz = tool.parser.get_moov_size()
    mp4_metadata = byterange_request(url, start_byte=0, end_byte=moov_sz)
    tool.parser.set_binary(mp4_metadata)
    tool.parser.parse()

    sp_timestamp = float(math.floor(conver_timestr_to_timestamp(sp)))
    ep_timestamp = conver_timestr_to_timestamp(ep) + 1.00

    if sp_timestamp < 0 or ep_timestamp < 0:
        assert False

    ftyp_raw, moov_raw, mdat_raw, trim_result = tool.live_trim(url, sp_timestamp, ep_timestamp, byterange_request, sync=True)
    _raw = b'' + ftyp_raw + moov_raw + mdat_raw
    return _raw, trim_result

def sync_trimmed_video(media_file, trim_result):
    sync_delta = trim_result['video_track']['res_start_time'] - trim_result['sound_track']['res_start_time']
    #ffmpeg_sync_cmd = "ffmpeg -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a -acodec copy -vcodec copy {out_file}"
    ffmpeg_sync_cmd = "{ffmpeg} -y -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a {codec1} copy {codec2} copy {out_file}"
    codec1 = '-vcodec'
    codec2 = '-acodec'
    if sync_delta >= 0:
        codec1 = '-acodec'
        codec2 = '-vcodec'
    n, ext = os.path.splitext(media_file)
    out_file = n + "_sync" + ext
    cmd = ffmpeg_sync_cmd.format(ffmpeg=ffmpeg_bin, video_file=media_file, ts=sync_delta, audio_file=media_file, out_file=out_file, codec1=codec1, codec2=codec2)
    child = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = child.communicate()
    if not os.path.exists(out_file):
        return None

    return out_file

def lambda_handler(event, context):
    """Sample pure Lambda function
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
    """
    resp = {
        "statusCode": 400,
        "body": {}
    }
    params = get_body_parameters(event, 'url', 'sp', 'ep')
    if not params:
        resp['body'] = json.dumps({
            "success": False,
            "err": "invalid parameter"
        })
        return resp
        
    try:
        raw, trim_result = live_trim(params['url'], params['sp'], params['ep'])
    except Exception as e:
        resp['body'] = json.dumps({
            "success": False,
            "err": "fail to process trimming, invalid request"
        })
        return resp
    
    s3_client = create_s3_client_object()
    bucket_name = get_dest_bucket()
    """
    check raw size over 400mb
    then, write to s3 not temp
    """
    tmp_file_name = hashlib.sha256(params['url'].encode()).hexdigest() + ".mp4"
    used = get_directory_usage('/tmp')
    s3_uploaded = False
    if used >= (230 * 1024 * 1024): # if used lambda temporary space is over 230mb
        s3_key = "{}/{}".format(tmp_path_s3_key, tmp_file_name)
        try:
            s3_put_object_wrapper(s3_client, bucket_name, s3_key, raw)
        except Exception as e:
            resp['statusCode'] = 500
            resp['body'] = json.dumps({
                "success": False,
                "err": "fail to process trimming, invalid request"
            })
            return resp
        
        s3_signed_url = get_s3_presigned_url(
            s3_client=s3_client, 
            bucket=bucket_name,
            s3_key=s3_key)
        tmp_file_path = s3_signed_url
        s3_uploaded = True
    else:
        tmp_file_path = write_at_lambda_storage(tmp_file_name, raw)
    del raw
    out_file = sync_trimmed_video(tmp_file_path, trim_result)
    
    if not out_file:
        resp['statusCode'] = 500
        resp['body'] = json.dumps({
            "success": False,
            "err": "fail to process trimming, internal sever error"
        })
        return resp
    
    if not s3_uploaded:
        os.remove(tmp_file_path)
    """
    upload synced file 
    """
    result_s3_key = "{}/{}".format(result_path_s3_key, os.path.basename(out_file))
    signed_url = s3_upload_file_wrapper(
                    s3_client=s3_client,
                    bucket=bucket_name,
                    source=out_file,
                    s3_key=result_s3_key
                )

    resp['statusCode'] = 200
    resp['body'] = json.dumps({
        "success": True,
        "data": {
            "url": signed_url
        }
    })
    
    return resp
