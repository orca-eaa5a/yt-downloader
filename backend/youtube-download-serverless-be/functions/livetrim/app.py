import os
import gc
import re
import ssl
import hashlib
import logging

from awsutils.aws_util import *
from mp4parser.utils.utils import *
from mp4parser.utils.ffmpeg_utils import *
from mp4parser.mp4modifier import Mp4Modifier
from mp4parser.mp4parse import Mp4Parser

logging.getLogger().setLevel(logging.INFO)

BUCKET_NAME = os.environ.get('VIDEO_SAVED_BUCKET')
TRACKINFO_SAVED_TABLE = os.environ.get('TRACKINFO_SAVED_TABLE')
TRACKINFO_SAVED_TABLE_PARTITION_KEY = os.environ.get('TRACKINFO_SAVED_TABLE_PARTITION_KEY')
TRACKINFO_SAVED_TABLE_SORT_KEY = os.environ.get('TRACKINFO_SAVED_TABLE_SORT_KEY')
TRACKINFO_SAVED_TABLE_GSI = os.environ.get('TRACKINFO_SAVED_TABLE_GSI')

SIGNED_URL_TIMEOUT = 600
tmp_path_s3_key = 'tmp'
result_path_s3_key = 'result'

ssl._create_default_https_context = ssl._create_unverified_context

def get_unique_track_id(video_id, track_time):
    return hashlib.sha256("{}:{}".format(video_id, track_time).encode()).hexdigest()


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
        'statusCode': 400,
        'body': {
            'success': False
        }
    }
    params, msg = get_body_parameters(event, 'o_url', 'url', 'sp', 'ep')
    if not params:
        resp['body']['err'] = msg
        logging.error(resp['body']['err'])
        return resp
        
    parser = Mp4Parser()
    try:
        parser.stream_parse(params['url'])
        parser.make_samples_info()
    except Exception as e:
        resp['body']['err'] = str(e)
        logging.error("error at parse stream {}: source: ".format(e, params['o_url']))
        return resp

    modifier = Mp4Modifier(parser)
    sp = conver_timestr_to_timestamp(params['sp'])
    ep = conver_timestr_to_timestamp(params['ep'])
    duration = ep - sp
    try:
        mp4_header, mdat, trim_result = modifier.livetrim(params['url'], sp, ep + 1.0, True)
    except Exception as e:
        resp['body']['err'] = "fail to process trimming with error: {}".format(str(e))
        logging.error("error at livetrim {}: source: ".format(e, params['o_url']))
        return resp
    
    raw = mp4_header + mdat
    
    del mp4_header
    del mdat
    del modifier
    del parser

    gc.collect()
    logging.info('process garbage collecting')

    s3_client = get_s3_client()
    bucket_name = BUCKET_NAME
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
    try:
        out_file, m_sp = ffmpeg_sync(tmp_file_path, trim_result)
        if not out_file:
            logging.error("ffmpeg_sync failed: {} / {}-{}".format(params['url'], params['sp'], params['ep']))
            resp['statusCode'] = 500
            resp['body']['err'] = "fail to process sync, internal sever error"

            return resp

    except Exception as e:
        resp['statusCode'] = 500
        resp['body']['err'] = "fail to process sync with error: {}".format(str(e))
        logging.error("ffmpeg_sync failed: {} / {}-{} with error: {}".format(params['url'], params['sp'], params['ep'], str(e)))
        return resp
    
    if not s3_uploaded:
        os.remove(tmp_file_path)
    
    """
    cutoff_extra_frames about synced file 
    """
    s_sp = sp - m_sp
    tmp_file_path = out_file
    try:
        out_file = ffmpeg_cutoff_extra_times(tmp_file_path, s_sp, duration)
        if not out_file:
            logging.error("ffmpeg_cutoff_extra_times failed: {} / {}-{}".format(params['url'], params['sp'], params['ep']))
            resp['statusCode'] = 500
            resp['body']['err'] = "fail to process cutoff extra frame"
            return resp

        os.remove(tmp_file_path)

    except Exception as e:
        logging.error("ffmpeg_cutoff_extra_times failed: {} / {}-{} with error: {}".format(params['url'], params['sp'], params['ep'], str(e)))
        resp['statusCode'] = 500
        resp['body']['err'] = "fail to process sync with error: {}".format(str(e))

        return resp
    
    out_file = "{}_{}-{}".format(out_file, int(sp),int(ep))
    result_s3_key = "{}/{}".format(result_path_s3_key, os.path.basename(out_file))
    try:
        region, bucket_name, s3_key = s3_upload_file_wrapper(
                        s3_client=s3_client,
                        bucket=bucket_name,
                        source=out_file,
                        s3_key=result_s3_key,
                        content_type='video/mp4',
                        acl='public-read'
                    )
    except Exception as e:
        resp['statusCode'] = 500
        resp['body'] = {
            "success": False,
            "err": "fail to put object at {}".format(bucket_name)
        }
        logging.error("fail to put object at {}/{} with {}".format(bucket_name, s3_key, str(e)))
        return resp
        
    logging.info("trimmed result is uploaded at {}/{}".format(bucket_name, result_s3_key))
    
    regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
    video_id = regex.search(params['o_url']).group(1)
    dyn_client = get_dynamodb_client()
    sort_key = "{}-{}".format(int(sp),int(ep))
    unq_track_id = get_unique_track_id(video_id, sort_key)
    
    resp = dyn_put_item(
        dyn_client=dyn_client,
        table_name=TRACKINFO_SAVED_TABLE,
        item={
            'Item':{
                TRACKINFO_SAVED_TABLE_PARTITION_KEY: {
                    'S': video_id
                },
                TRACKINFO_SAVED_TABLE_SORT_KEY: {
                    'S': sort_key
                },
                'BucketName':{
                    'S': bucket_name
                },
                'S3Key':{
                    'S': s3_key
                },
                TRACKINFO_SAVED_TABLE_GSI:{
                    'S':unq_track_id
                }
            }
        }
    )
    if resp:
        logging.info("livetrim finished: {} / is saved at {}".format(result_s3_key, bucket_name))
        resp['statusCode'] = 200
        resp['body'] = {
            "success": True,
            "data": {
                "bucket_region": region,
                "bucket": bucket_name,
                "s3_key": s3_key
            }
        }
    else:
        logging.error("livetrim failed: {} / is not saved at {}".format(result_s3_key, bucket_name))
        resp['body']['err'] = "fail to save data at dynamodb"
    return resp


# if __name__ == '__main__':
#     lambda_handler(
#         event={
#             "statusCode": 200,
#             "body": {
#                 "exist": False,
#                 "data": {
#                     "o_url": "https://www.youtube.com/watch?v=HRdXUfpPGLI&t=13796s",
#                     "url": "https://rr3---sn-n3cgv5qc5oq-bh2s7.googlevideo.com/videoplayback?expire=1674899054&ei=DZrUY-XgOreavcAPypKGyAU&ip=211.215.4.208&id=o-ALGure14o-YAtFaLnT0H4be8MQnpS-GghjdudqHsetCs&itag=22&source=youtube&requiressl=yes&mh=F_&mm=31%2C26&mn=sn-n3cgv5qc5oq-bh2s7%2Csn-oguelnz7&ms=au%2Conr&mv=m&mvi=3&pcm2cms=yes&pl=22&gcr=kr&initcwndbps=2073750&vprv=1&mime=video%2Fmp4&cnr=14&ratebypass=yes&dur=36389.569&lmt=1674752439750118&mt=1674877050&fvip=1&fexp=24007246&c=ANDROID&txp=5432434&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cgcr%2Cvprv%2Cmime%2Ccnr%2Cratebypass%2Cdur%2Clmt&sig=AOq0QJ8wRgIhAOy9wRQiQNXyftoB5lsCD35ogoDD5KD6mTN5FXCIrN3bAiEAnvA_EncA-vX9rChqio8ig7h-iT1fiVsLuOL-C66HMuQ%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAOy5MfuFvS8r48gsgrXGPHC4jvaPv_lExbs_oEyXxVPdAiEAr9plNLzxXPtbsxCKzCYghPA08qbwl4B8OpI11VmvI8g%3D",
#                     "sp": "03:47:11.0",
#                     "ep": "03:49:55.7"
#                 }
#             }
# }, context=None
#     )