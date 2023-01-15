import re
import ssl
from flask import Flask, request, jsonify, make_response
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from mp4parser import MpegTool, PyMp4Wrapper
from utils import byterange_request, conver_timestr_to_timestamp

app = Flask(__name__)
ssl._create_default_https_context = ssl._create_unverified_context
timeline_regex = re.compile('([0-9]+:)?[0-5]?[0-9]:[0-5][0-9]')

@app.route('/search', methods=['GET'])
def query_youtube():
    q = request.args.get('q')
    if not q:
        resp = make_response(
            jsonify({ 'success': False, 'msg': 'empty query request' }),
            200
        )
        return resp
    try:
        url = q
        if not url.startswith('https'):
            url = 'https://www.youtube.com/watch?v={}'.format(q)
        yt = YouTube(url)
    except RegexMatchError as rme:
        return make_response(
            jsonify({
                'success': False,
                'msg': 'invalid youtube id form'
            }),
            400
        )
    
    """
    parse timestamp
    """
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

    return make_response(
        jsonify({
            'success': True,
            'data': yt_info
        }),
        200
    )

@app.route('/livetrim', methods=['POST'])
def trim_yt_video():
    if not request.is_json:
        return make_response(
                jsonify({
                    'success': False,
                    'msg': 'invalid request parameter format'
                }), 400
            )
    params = request.get_json()
    video_url = params['url']
    sp = params['start']
    ep = params['end']

    tool = MpegTool()
    chunk_sz = 0
    # at first read its header
    chunk_sz = 100 # only read first 100 byte
    content = byterange_request(video_url, start_byte=0, end_byte=chunk_sz)
    tool.parser.set_binary(content)
    moov_sz = tool.parser.get_moov_size()
    mp4_metadata = byterange_request(video_url, start_offset=0, end_offset=moov_sz)

    tool.parser.set_binary(mp4_metadata)
    # re-parse full mp4 header
    tool.parser.parse()

    ftyp_raw, moov_raw, mdat_raw, trim_result = tool.live_trim(video_url, '1:00', 80, byterange_request, sync=True)

@app.route('/rawtrim', methods=['POST'])
def trim_raw_video():
    if not request.is_json:
        return make_response(
                jsonify({
                    'success': False,
                    'msg': 'invalid request parameter format'
                }), 400
            )
    params = request.get_json()
    video_url = params['url']
    sp = params['start']
    ep = params['end']


if __name__ == '__main__':
    app.run(debug=True)