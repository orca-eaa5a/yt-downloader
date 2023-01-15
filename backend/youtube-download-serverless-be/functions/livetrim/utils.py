import requests
import logging

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
        logging.error('[byterange_request] invalid parameter')
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
            logging.error('[byterange_request] request failed with error')
            logging.error('[%d] %s' % (resp.status_code, resp.text))
            assert False
    
    return _bin