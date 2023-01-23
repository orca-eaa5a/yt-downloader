import os
import ssl
import hashlib
import json

from awsutils.aws_util import *
from mp4parser.utils.utils import *
from mp4parser.utils.ffmpeg_utils import *
from mp4parser.mp4modifier import Mp4Modifier
from mp4parser.mp4parse import Mp4Parser

SIGNED_URL_TIMEOUT = 600
tmp_path_s3_key = 'tmp'
result_path_s3_key = 'result'

ssl._create_default_https_context = ssl._create_unverified_context

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
        
    parser = Mp4Parser()
    parser.stream_parse(params['url'])
    parser.make_samples_info()

    modifier = Mp4Modifier(parser)
    sp = conver_timestr_to_timestamp(params['sp'])
    ep = conver_timestr_to_timestamp(params['ep'])
    duration = ep - sp
    try:
        mp4_header, mdat, trim_result = modifier.livetrim(params['url'], sp, ep + 1.0, True)
    except Exception as e:
        resp['body'] = json.dumps({
            "success": False,
            "err": "fail to process trimming, invalid request"
        })
        return resp
    
    raw = mp4_header + mdat
    del mp4_header
    del mdat

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
    out_file, m_sp = ffmpeg_sync(tmp_file_path, trim_result)
    
    if not out_file:
        resp['statusCode'] = 500
        resp['body'] = json.dumps({
            "success": False,
            "err": "fail to process sync, internal sever error"
        })
        return resp
    
    if not s3_uploaded:
        os.remove(tmp_file_path)
    
    """
    cutoff_extra_frames about synced file 
    """
    s_sp = sp - m_sp
    tmp_file_path = out_file
    out_file = ffmpeg_cutoff_extra_times(tmp_file_path, s_sp, duration)
    if not out_file:
        resp['statusCode'] = 500
        resp['body'] = json.dumps({
            "success": False,
            "err": "fail to process cutoff extra frame"
        })
    os.remove(tmp_file_path)

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
