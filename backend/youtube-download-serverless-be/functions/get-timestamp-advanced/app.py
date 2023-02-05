import re
import json
import logging
import requests

logging.getLogger().setLevel(logging.INFO)

YOUTUBE_API_KEY = "AIzaSyCpADRn50KXSimEQLh7-egvesN21qWwoQ8"

def get_querystring_params(event, *args):
    params = {}
    for arg in args:
        if arg in event:
            params[arg] = event[arg]
    return params
    # if 'queryStringParameters' in event:
    #     params = {}
    #     for arg in args:
    #         if arg in event['queryStringParameters']:
    #             params[arg] = event['queryStringParameters'][arg]
    #     return params
    # return None

def lambda_handler(event, context):
    resp = {
        'statusCode':400,
        'body':{
            'success':False,
            'data': None
        }
    }
    params = get_querystring_params(event, 'url')
    if not params:
        logging.error('invalid parameter')
        resp['body']['err'] = 'invalid parameter'
        return resp
    
    vid = None
    video_url = params['url']
    
    if video_url.startswith("https"):
        # requested with youtube video url
        regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
        vid = regex.search(video_url).group(1)

    if not vid:
        logging.error('invalid parameter')
        resp['err'] = 'invalid parameter'
        return resp
    
    get_resp = requests.get(
        "https://www.googleapis.com/youtube/v3/commentThreads?videoId={}&key={}&part=snippet&maxResults=100&order=relevance".format(vid, YOUTUBE_API_KEY)
    )
    yt_comment_info = None
    if get_resp.status_code == 200 and get_resp.ok:
        logging.info('success to request youtube comment threads ')
        yt_comment_info = json.loads(get_resp.text)
        items = yt_comment_info['items']
        comments = []
        timeline_regex = re.compile('([0-9]+:)?[0-5]?[0-9]:[0-5][0-9]')
        for item in items:
            comments.append(
                {
                    'text': item['snippet']['topLevelComment']['snippet']['textOriginal'],
                    'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount']
                }
            )
        comments = sorted(comments, key=lambda d: d['likeCount'], reverse=True)[:20]
        data = []
        for comment in comments:
            s = timeline_regex.search(comment['text'])
            if not s:
                continue
            for line in comment['text'].split("\n"):
                r = timeline_regex.search(line)
                if not r:
                    continue
                data.append({
                    'timestamp': r[0],
                    'tag': line.replace(r[0], "")
                })
        resp['body']['success'] = True
        resp['body']['data'] = data
        resp['statusCode'] = 200
    else:
        logging.info('fail to request youtube comment threads ')
        resp['err'] = 'fail to get youtube comment thread'
    
    return resp

# if __name__ == '__main__':
#     lambda_handler(event={
#         'queryStringParameters':{
#             'url':'https://youtube.com/watch?v=48gctUFeMzA'
#         }
#     }, context=None)
