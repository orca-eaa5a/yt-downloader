import re
import json
from pytube import YouTube
from pytube.exceptions import RegexMatchError
import requests

def get_querystring_param(event, param):
    if 'queryStringParameters' in event:
        if param in event['queryStringParameters']:
            return event['queryStringParameters'][param]
    return None

def make_video_info(yt:YouTube):
    timeline_regex = re.compile('([0-9]+:)?[0-5]?[0-9]:[0-5][0-9]')
    full_desc = yt.vid_info['videoDetails']['shortDescription']
    desc_lines = full_desc.split("\n")
    time_info = []
    streams = []
    for line in desc_lines:
        res = timeline_regex.search(line)
        if res:
            time_info.append({
                'timestamp': res[0],
                'tag': line.replace(res[0], "")
            })
    _streams = yt.vid_info['streamingData']['formats']
    for s in _streams:
        streams.append({
            'url': s['url'],
            'mime_type': s['mimeType'].split(";")[0],
            'quality': s['qualityLabel']
        })
    yt_info = {
        'vid': yt.vid_info['videoDetails']['videoId'],
        'title': yt.vid_info['videoDetails']['title'],
        'length':  yt.vid_info['videoDetails']['lengthSeconds'],
        'thumbnail': yt.vid_info['videoDetails']['thumbnail']['thumbnails'][-1]['url'],
        'time_info': time_info,
        'streams': streams
    }

    return yt_info

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
    q = get_querystring_param(event, 'q')
    if not q:
        resp['statusCode'] = 200
        resp['body'] = json.dumps(
            {'success': False, 'msg': 'empty query request'}
        )
        return resp
    try:
        url = q
        if not url.startswith('https'):
            url = 'https://www.youtube.com/watch?v={}'.format(q)
        yt = YouTube(url)
    except RegexMatchError as rme:
        resp['statusCode'] = 400
        resp['body'] = json.dumps({
            'success': False,
            'msg': 'invalid youtube id form'
        })
        return resp
    
    video_info = make_video_info(yt)
    resp['statusCode'] = 200
    resp['body'] = json.dumps({
        'success': True,
        'data': video_info
    })

    return resp
