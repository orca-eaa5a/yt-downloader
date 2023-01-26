import os
import re
import ssl
import json
import hashlib
import logging

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
    params = get_body_parameters(event, 'o_url', 'url', 'sp', 'ep')
    if not params:
        resp['body'] = {
            "success": False,
            "err": "invalid parameter"
        }
        logging.error("invalid parameter")
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
        resp['body'] = {
            "success": False,
            "err": "fail to process trimming, invalid request"
        }
        logging.error("fail to process trimming.. with {}".format(str(e)))
        return resp
    
    raw = mp4_header + mdat
    del mp4_header
    del mdat

    s3_client = get_s3_client()
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
            resp['body'] = {
                "success": False,
                "err": "fail to put object at {}".format(bucket_name)
            }
            logging.error("fail to put object at {}/{} with {}".format(bucket_name, s3_key, str(e)))
            return resp
        
        s3_signed_url = get_s3_presigned_url(
            s3_client=s3_client, 
            bucket=bucket_name,
            s3_key=s3_key)
        tmp_file_path = s3_signed_url
        s3_uploaded = True
        logging.info("file is uploaded at {}/{}".format(bucket_name, tmp_file_path))
    else:
        tmp_file_path = write_at_lambda_storage(tmp_file_name, raw)
    
    del raw
    out_file, m_sp = ffmpeg_sync(tmp_file_path, trim_result)
    
    if not out_file:
        resp['statusCode'] = 500
        resp['body'] = {
            "success": False,
            "err": "fail to process sync, internal sever error"
        }
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
        resp['body'] = {
            "success": False,
            "err": "fail to process cutoff extra frame"
        }
        logging.error("fail to process cutoff extra frame")
    os.remove(tmp_file_path)

    result_s3_key = "{}/{}".format(result_path_s3_key, os.path.basename(out_file))
    region, bucket_name, s3_key = s3_upload_file_wrapper(
                    s3_client=s3_client,
                    bucket=bucket_name,
                    source=out_file,
                    s3_key=result_s3_key
                )
    logging.info("trimmed result is uploaded at {}/{}".format(bucket_name, result_s3_key))
    
    regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
    video_id = regex.search(params['o_url']).group(1)
    dyn_client = get_dynamodb_client()
    resp = dyn_put_item(
        dyn_client,
        key=video_id,
        sort_key="{}-{}".format(int(sp),int(ep)),
        bucket_name=bucket_name,
        s3_key=result_s3_key
    )
    if resp:
        logging.info("trim result lookup is saved at DynamoDB")

    resp['statusCode'] = 200
    resp['body'] = {
        "success": True,
        "data": {
            "bucket_region": region,
            "bucket": bucket_name,
            "s3_key": s3_key
        }
    }

    return resp


if __name__ == '__main__':
    lambda_handler(
        event={
  "statusCode": 200,
  "body": {
    "exist": False,
    "data": {
      "o_url": "https://www.youtube.com/watch?v=H4bhRn2c8Cc",
      "url": "https://rr5---sn-p5qlsn7s.googlevideo.com/videoplayback?expire=1674747054&ei=TkjSY_SjL8vr8wSul4Iw&ip=18.215.62.225&id=o-AH8Mjf9Fa6gI6Nfm-tRANhZSoUTWwluOfMtFxbNNga-N&itag=22&source=youtube&requiressl=yes&mh=bs&mm=31%2C26&mn=sn-p5qlsn7s%2Csn-vgqsknz7&ms=au%2Conr&mv=m&mvi=5&pl=23&pcm2=yes&gcr=us&initcwndbps=691250&vprv=1&mime=video%2Fmp4&cnr=14&ratebypass=yes&dur=1440.983&lmt=1633373905635161&mt=1674725113&fvip=2&fexp=24007246&c=ANDROID&txp=5416222&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cpcm2%2Cgcr%2Cvprv%2Cmime%2Ccnr%2Cratebypass%2Cdur%2Clmt&sig=AOq0QJ8wRQIgUEK8-farK6OwHBHgwew1QZ9HYt-GyADQCpTqEA4WFRACIQDFsSog3JQR3Uu1QmdN_xGYZj8iXqDM1NRhzKgFZKxlkg%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRAIgQKZfyRLIH8v8iwcwhwBzAIZlNojkjxEy3J36SRy6sxcCIGq5hgPckjrrmI2kArZEB5vx9E6Vl20EYBLwtZosLQyJ",
      "sp": "00:15:12",
      "ep": "00:20:40"
    }
  }
}, context=None
    )