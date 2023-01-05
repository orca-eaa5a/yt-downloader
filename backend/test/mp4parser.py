import logging
import copy
from header import *
from pymp4.parser import Box
from pymp4.util import BoxUtil

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class PyMp4Wrapper(object):
    def __init__(self) -> None:
        self.ftype = None
        self.moov = None
        self.mdat = None
        self.raw = None
        self.sample_arr = {
            'video_track': [],
            'sound_track': [],
        }
        self.chunk_arr = {
            'video_track': [],
            'sound_track': [],
        }
        self.video_track = None
        self.media_track = None
        pass

    def set_binary(self, binary:bytes):
        if not binary:
            logging.error('[set_binary] null binary')
            assert 0
        self.raw =binary
        pass

    def parse(self):
        try:
            self.ftype = Box.parse(self.raw)
        except OSError as e:
            logging.error('[parse] invalid mp4 format binary')
            assert 0

        try:
            self.moov = Box.parse(self.raw[self.ftype.end:])
        except OSError as e:
            logging.error('[parse] invalid mp4 format binary or moov header is not located in front of the mdat')
            assert 0
        self.mdat = self.raw[self.moov.end:]

        # set track
        track_list = list(BoxUtil.find(self.moov, b'trak'))
        for trak in track_list:
            if BoxUtil.first(trak, b'hdlr').handler_type == b'vide':
                self.video_track = trak
            else:
                self.sound_track = trak

        self.make_chunk_arr()


    def get_running_time(self, track='video_track'):
        track_duration = BoxUtil.first(getattr(self, track), b'mdhd').duration
        track_timescale = BoxUtil.first(getattr(self, track), b'mdhd').timescale

        return int(track_duration/track_timescale)

    def get_chunk_arr(self, track='video_track'):
        return getattr(self, 'chunk_arr')[track]
    
    def get_sample_arr(self, track='video_track'):
        return getattr(self, 'sample_arr')[track]

    def get_chunk_count(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stco').entry_count

    def get_chunk_info_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stsc').entries
    
    def get_chunk_offset_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stco').entries

    def get_sample_size_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stsz').entry_sizes
    
    def get_sample_atom_arr(self, track='video_track'):
        return BoxUtil.first(getattr(self, track), b'stts').entries

    def make_chunk_arr(self, track='video_track'):
        # chunk timestamp, chunk offset, chunk size number_of_samples, prev_sample_count
        chunk_info_arr = self.get_chunk_info_arr(track)
        sample_size_arr = self.get_sample_size_arr(track)
        chunk_offset_arr = self.get_chunk_offset_arr(track)
        sample_per_sec_arr = self.get_samples_per_sec_arr(track)

        chunk_info_arr_idx = 0
        sample_per_sec_arr_idx = 0
        sample_count = 0
        timestamp = 0
        next_chunk_info = None
        for chunk_idx in range(len(chunk_offset_arr)):
            try:
                if not next_chunk_info:
                    next_chunk_info = chunk_info_arr[chunk_info_arr_idx+1]
                if next_chunk_info['first_chunk'] == chunk_idx+1:
                    chunk_info_arr_idx += 1
                    next_chunk_info = chunk_info_arr[chunk_info_arr_idx+1]
            except IndexError as ie:
                next_chunk_info = None
                pass
            finally:
                cur_chunk_info = chunk_info_arr[chunk_info_arr_idx]
            chunk_size = 0
            for i in range(cur_chunk_info['samples_per_chunk']):
                self.sample_arr[track].append(
                    {
                        'chunk_idx':  chunk_idx,
                        'sample_idx': sample_count,
                        'sample_offset': chunk_offset_arr[chunk_idx].chunk_offset + chunk_size, 
                        'sample_size': sample_size_arr[sample_count]
                    }
                )
                chunk_size += sample_size_arr[sample_count]
                sample_count += 1
            base_sample_index = sample_count - cur_chunk_info['samples_per_chunk']
            if base_sample_index > sample_per_sec_arr[sample_per_sec_arr_idx]['sample_count']:
                sample_per_sec_arr_idx+=1
            
            timestamp = base_sample_index/sample_per_sec_arr[sample_per_sec_arr_idx]['samples_per_sec']

            self.chunk_arr[track].append({
                'chunk_idx': chunk_idx,
                'chunk_offset': chunk_offset_arr[chunk_idx].chunk_offset,
                'start_sample_idx': base_sample_index,
                'number_of_samples': cur_chunk_info['samples_per_chunk'],
                'chunk_size': chunk_size,
                'timestamp': timestamp
            })

    def get_samples_per_sec_arr(self, track='video_track'):
        """
        동영상 1초 몇개의 sample이 필요한지 계산
        ret:
        [
            {
                'sample_count'
                'duration' # second
                'sample_delta'
            },
            ...
        ]
        """
        ret = []
        track_sample_atom_arr = self.get_sample_atom_arr(track)
        track_duration = BoxUtil.first(getattr(self, track), b'mdhd').duration
        track_timescale = BoxUtil.first(getattr(self, track), b'mdhd').timescale
        for atom in track_sample_atom_arr:
            if atom and track_duration <= 0:
                logger.error('[get_sample_count_per_sec] : 뭔가 잘못 됨')
                assert False

            if track_duration < atom['sample_count'] * atom['sample_delta']:
                break
            else:
                ret.append(
                    {
                        'sample_count': atom['sample_count'],
                        'sample_delta': atom['sample_delta'],
                        'samples_per_sec': int(track_timescale / atom['sample_delta']),
                        'duration': int((atom['sample_count'] * atom['sample_delta'])/track_timescale)
                    }
                )
                track_duration -= atom['sample_count'] * atom['sample_delta']

        return ret

    def get_chunk_by_sample_index(self, sample_index, track='video_track'):
        """
        sample_index를 기반으로, sample이 포함된 chunk를 가져옵니다.
        ! sample_index는 0부터 시작합니다.

        ret:
        
        """
        for chunk_i in self.get_chunk_arr(track):
            if chunk_i['start_sample_idx'] <= sample_index and sample_index < chunk_i['start_sample_idx'] + chunk_i['number_of_samples']:
                return chunk_i
        logging.error('[get_chunk_by_sample_index] invalid index')
        assert False

    def get_chunk_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 chunk를 가져옵니다.
        ! index는 1부터 시작합니다

        ret:
        'chunk_idx': chunk_idx,
        'chunk_offset': start file offset of chunk
        'start_sample_idx': start offset of sample in chunk
        'number_of_samples': number of samples that chunk contained
        'chunk_size': chunk_size,
        'timestamp': timestamp of video that chunk coresspond
        """
        try:
            return self.get_chunk_arr(track)[index]
        except IndexError as ie:
            logging.error('[get_chunk_by_index] invalid index')
        assert False

    def get_chunk_by_time(self, time_str, track='video_track'):
        """
        desc:
        시간 값에 맞는 chunk를 가져옵니다.
        시간 값에 해당하는 sample이 chunk의 시작 sample이 아닐 경우,
        chunk의 시작 sample을 가져옵니다.
        ! millisecond는 무시합니다

        ret:
        chunk_offset, chunk_size, sample_index, samples_per_chunk
        """
        timestamp, _pow = 0, 0
        sample_arr = self.get_sample_arr(track)
        try:
            time_arr = [int(f) for f in time_str.split(':')]
        except ValueError as ve:
            logger.error('[get_chunk_by_time] : invalid time format')
            assert False
        time_arr.reverse()
        for t in time_arr:
            timestamp += pow(60, _pow) * t
        del time_arr

        done = False
        chunk_arr = self.get_chunk_arr(track)
        prev_chunk_i = chunk_arr[0]
        for chunk_i in chunk_arr:
            if chunk_i['timestamp'] > timestamp:
                done = True
                break
            prev_chunk_i = chunk_i
        
        if timestamp != 0 and not done:
            logger.error('[get_chunk_by_time] : timestamp is not in duration')
            assert False

        return prev_chunk_i

    def get_chunk_by_offset(self, offset, track='video_track'):
        """
        desc:
        offset에 맞는 chunk를 가져옵니다.
        offset에 해당하는 sample이 chunk의 시작 sample이 아닐 경우,
        chunk의 시작 sample을 가져옵니다.

        ret:
        chunk_offset, chunk_size, samples_per_chunk
        """
        done = False
        chunk_arr = self.get_chunk_arr(track)
        prev_chunk_i = chunk_arr[0]
        for chunk_i in chunk_arr:
            if chunk_i['chunk_offset'] > offset:
                done = True
                break
        if not done:
            logger.error('[get_chunk_by_offset] : invalid offset')
            assert False
        
        return prev_chunk_i

    def get_sample_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """
        try:
            sample = self.get_sample_arr(track)[index]
        except IndexError as ie:
            logger.error('[get_sample_by_index] : invalid index')
            assert False

        return sample

    def get_sample_by_offset(self, offset, track):
        """
        desc:
        offset에 맞는 sample을 가져옵니다.
        offset이 sample의 시작 지점이 아닐 경우, 범위 내에 offset을 포함하는
        sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """
        chunk = self.get_chunk_by_offset(offset, track)
        idx = 0
        sample_arr = self.get_sample_arr(track)
        _prev = sample_arr[chunk['start_sample_idx']]
        for sample in sample_arr[chunk['start_sample_idx']:]:
            if chunk['number_of_samples'] == idx:
                logger.error('[get_sample_by_offset] : invalid offset')
                assert False
            idx += 1
            if sample['sample_offset'] > offset:
                return _prev
            _prev = sample
        
        assert False

class MpegTool(object):
    def __init__(self) -> None:
        self.parser = PyMp4Wrapper()
        pass

    def trim(self, src, start_timestamp, duration):
        """
        src : mp4 header가 포함된 binary
        start_timestamp : trim의 시작지점
        duration : trim한 동영상의 running time
        """
        
        def edit_stts(track, parser, track_type:str):
            
            chunk_i = parser.get_chunk_by_time(start_timestamp, track_type)
            stts = BoxUtil.first(track, b'stts')
            stts_etry = stts.entries
            removed_sample_count = chunk_i['start_sample_idx']
            
            for s in stts_etry:
                tmp = s['sample_count']
                s['sample_count'] -= removed_sample_count
                removed_sample_count -= tmp
                if removed_sample_count <= 0:
                    break
            
            idx = 0
            while True:
                if stts_etry[idx]['sample_count'] == 0:
                    stts_etry.pop(idx)
                    idx-=1
                else:
                    break
                idx+=1
            
            return stts

        self.parser.set_binary(src)
        self.parser.parse()

        new_moov_header = copy.deepcopy(self.parser.moov)
        video_track = None
        sound_track = None
        track_list = list(BoxUtil.find(new_moov_header, b'trak'))
        for trak in track_list:
            if BoxUtil.first(trak, b'hdlr').handler_type == b'vide':
                video_track = trak
            else:
                sound_track = trak
        
        if video_track:
            edit_stts(video_track, self.parser, 'video_track')
        if sound_track:
            edit_stts(video_track, self.parser, 'sound_track')
        
        # step2 > stsc 수정
        # - 현재 chunk 앞에 몇 개의 chunk가 있는지 확인 후, stsc 헤더 수정
        
        
        # 현재 chunk 앞에 몇 개의 sample이 있는지 확인 후, stts 헤더 수정
        # - 지워지는 sample 만큼 sample_count 삭제




if __name__ == '__main__':
    _bin = b''
    with open('./video_source/0-3.mp4', 'rb') as f:
        _bin = f.read()
    # parser = PyMp4Wrapper()
    # parser.set_binary(_bin)
    # parser.parse()
    # print(parser.get_chunk_by_sample_index(74))
    tool = MpegTool()
    tool.trim(_bin, '2', 4)
    pass