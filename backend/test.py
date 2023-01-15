import ssl
import math
import logging
import requests
from utils import *
import subprocess
from pytube import YouTube
from mp4parser import MpegTool, PyMp4Wrapper

ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger()
logger.setLevel(logging.INFO)
    
def live_trim(url, sp, ep):
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
    
    print(trim_result)

    with open('./live_download.mp4', 'wb') as f:
        f.write(ftyp_raw)
        f.write(moov_raw)
        f.write(mdat_raw)
    
    video_url = './live_download.mp4'
    return video_url, trim_result

    """
    if timestamp == 0 and duration == 0:
        # download full video
        pass
    elif timestamp and duration == 0:
    """

def sync_trimmed_video(url, trim_result):
    sync_delta = trim_result['video_track']['res_start_time'] - trim_result['sound_track']['res_start_time']
    #ffmpeg_sync_cmd = "ffmpeg -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a -acodec copy -vcodec copy {out_file}"
    ffmpeg_sync_cmd = "ffmpeg -y -i {video_file} -itsoffset {ts} -i {audio_file} -map 0:v -map 1:a {codec1} copy {codec2} copy {out_file}"
    codec1 = '-vcodec'
    codec2 = '-acodec'
    if sync_delta >= 0:
        codec1 = '-acodec'
        codec2 = '-vcodec'
    cmd = ffmpeg_sync_cmd.format(video_file=url, ts=sync_delta, audio_file=url, out_file='trim_sync2.mp4', codec1=codec1, codec2=codec2)
    child = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = child.communicate()
    pass

def cutoff_extra_frames(url, sp, duration):
    import shutil
    import os
    f, ext = os.path.splitext(url)
    out_url = "{}{}{}".format(f,"_out", ext)
    
    ffmpeg_cutoff_comd = "ffmpeg -y -ss {sp} -i {video_file} -c copy -t {duration} {out_file}"
    cmd = ffmpeg_cutoff_comd.format(video_file=url, sp=sp, duration=duration, out_file=out_url)
    child = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = child.communicate()
    pass

def copy_file(url):
    import shutil
    import os
    f, ext = os.path.splitext(url)
    shutil.copyfile(url, "{}{}{}".format(f,"_copy", ext))

"""
아... video & aduio track이 붙어있는 경우만... 지원
smooth streaming 미지원
"""


# yt = YouTube('https://www.youtube.com/watch?v=MHvdCFbIdIQ')
# video_streams = yt.vid_info['streamingData']['formats']
# stream_url = video_streams[-1]['url']
# print(stream_url)


if __name__ == '__main__':
    url = 'https://rr6---sn-n3cgv5qc5oq-bh2l6.googlevideo.com/videoplayback?expire=1673731632&ei=0MnCY_XfIPuMvcAPuL2c6Ao&ip=211.215.4.208&id=o-ALwtXqnuutBlwI4vBNL330cleHKF6qBiQIlc4xoLtm4F&itag=22&source=youtube&requiressl=yes&mh=AI&mm=31%2C26&mn=sn-n3cgv5qc5oq-bh2l6%2Csn-ogul7n7s&ms=au%2Conr&mv=m&mvi=6&pl=22&initcwndbps=1192500&vprv=1&mime=video%2Fmp4&cnr=14&ratebypass=yes&dur=293.918&lmt=1640372759964016&mt=1673709664&fvip=3&fexp=24007246&c=ANDROID&txp=5311224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Ccnr%2Cratebypass%2Cdur%2Clmt&sig=AOq0QJ8wRgIhANSS8Wd7jGL6u4UHiLd-tmJ3mfzO0FUx0tKMGm6UdoDBAiEA_5gZsv8T3ea2Kx7kMEUtu0GZWqdoQERRTEqsacF8g60%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAOud_rV5eZHUSa6EjEBud_q5xz3lhc0PzTzcWUOBvv11AiEAralRwfgD1B0kB5zrLVV6mrqxBmQ-ENfW1YJYChTbSWE%3D'
    sp = '00:02:00.150'
    ep = '00:03:00.000'
    
    url, trim_result = live_trim(url, sp, ep)
    copy_file(url)
    sync_trimmed_video(url, trim_result)
    
    o_sp = conver_timestr_to_timestamp(sp)
    o_ep = conver_timestr_to_timestamp(ep)
    o_duration = o_ep-o_sp

    trim_sp = o_sp - trim_result['video_track']['res_start_time']
    cutoff_extra_frames(url, trim_sp, o_duration)
    print('done')

