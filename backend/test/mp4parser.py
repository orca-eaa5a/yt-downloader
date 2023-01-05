import logging
from header import *
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class MpegParser(object):
    class Track:
        video_track='video_track'
        sound_track='sound_track'

    def __init__(self) -> None:
        self.binary = None
        self.ftype = None
        self.moov = None
        self.mdat = None
        self.sample_arr = {
            MpegParser.Track.video_track: [],
            MpegParser.Track.sound_track: [],
        }
        self.chunk_arr = {
            MpegParser.Track.video_track: [],
            MpegParser.Track.sound_track: [],
        }
        pass

    def set_binary(self, _bin):
        self.binary = _bin
    
    def get_atombox_data(self, header, offset=0):
        _bin = self.binary[offset + ctypes.sizeof(AtomBoxHeader) : offset + header.size]
        return _bin

    def get_running_time(self, track='video_track'):
        track_duration = getattr(self.moov, track).mida.mdhd.duration
        track_timescale = getattr(self.moov, track).mida.mdhd.timescale

        return int(track_duration/track_timescale)

    def get_chunk_arr(self, track='video_track'):
        return self.chunk_arr[track]
    
    def get_sample_arr(self, track='video_track'):
        return self.sample_arr[track]

    def get_sample_atom_arr(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stts.sample_atom_arr

    def get_sample_count(self, track='video_track'):
        count = 0
        for atom in self.get_sample_atom_arr(track):
            count += atom['sample_count']
        return count

    def make_sample_arr(self, track='video_track'):
        chunk_info_arr = self.get_chunk_info_arr(track)
        sample_size_arr = self.get_sample_size_arr(track)
        chunk_offset_arr = self.get_chunk_offset_arr(track)
        sample_idx = 0
        if len(chunk_info_arr) == 1:
            pass
        else:
            prev_chunk_info = chunk_info_arr[0]
            for chunk_info in chunk_info_arr[1:]:
                number_of_chunks = chunk_info['first_chunk'] - prev_chunk_info['first_chunk']
                for idx in range(number_of_chunks):
                    i = 0
                    next_sample_offset = 0
                    while True:
                        if prev_chunk_info['samples_per_chunk'] <= i:
                            break
                        cur_chunk_idx = prev_chunk_info['first_chunk'] + idx
                        self.sample_arr[track].append(
                            {
                                'chunk_idx':  cur_chunk_idx,
                                'sample_idx': sample_idx,
                                'sample_offset': chunk_offset_arr[cur_chunk_idx-1] + next_sample_offset, 
                                'sample_size': sample_size_arr[sample_idx]
                            }
                        )
                        i+=1
                        sample_idx += 1
                        next_sample_offset += sample_size_arr[sample_idx]
                prev_chunk_info = chunk_info

        chunk_info = chunk_info_arr[-1]
        cur_chunk_idx = chunk_info['first_chunk']
        number_of_samples = self.get_sample_count(track)
        next_sample_offset = 0
        sample_per_chunk_cnt = 0
        while True:
            if number_of_samples <= sample_idx:
                break
            self.sample_arr[track].append({
                'chunk_idx':  cur_chunk_idx,
                'sample_idx': sample_idx,
                'sample_offset': chunk_offset_arr[cur_chunk_idx-1] + next_sample_offset, 
                'sample_size': sample_size_arr[sample_idx]
            })
            sample_per_chunk_cnt += 1
            next_sample_offset += sample_size_arr[sample_idx]
            sample_idx += 1
            if sample_per_chunk_cnt != 0 and (sample_per_chunk_cnt % chunk_info['samples_per_chunk'] == 0):
                cur_chunk_idx += 1

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
        for chunk_idx in range(1, len(chunk_offset_arr)+1):
            try:
                if not next_chunk_info:
                    next_chunk_info = chunk_info_arr[chunk_info_arr_idx+1]
                if next_chunk_info['first_chunk'] == chunk_idx:
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
                        'sample_offset': chunk_offset_arr[chunk_idx-1] + chunk_size, 
                        'sample_size': sample_size_arr[sample_count]
                    }
                )
                chunk_size += sample_size_arr[sample_count]
                print(chunk_idx, sample_count)
                sample_count += 1
            base_sample_index = sample_count - cur_chunk_info['samples_per_chunk']
            if base_sample_index > sample_per_sec_arr[sample_per_sec_arr_idx]['sample_count']:
                sample_per_sec_arr_idx+=1
            
            timestamp = base_sample_index/sample_per_sec_arr[sample_per_sec_arr_idx]['samples_per_sec']

            self.chunk_arr[track].append({
                'chunk_idx': chunk_idx,
                'chunk_offset': chunk_offset_arr[chunk_idx-1],
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
        track_duration = getattr(self.moov, track).mida.mdhd.duration
        track_timescale = getattr(self.moov, track).mida.mdhd.timescale
        for atom in track_sample_atom_arr:
            if atom and track_duration <= 0:
                logger.error('[get_sample_count_per_sec] : 뭔가 잘못 됨')
                assert False

            if track_duration < atom['sample_count'] * atom['duration']:
                break
            else:
                ret.append(
                    {
                        'sample_count': atom['sample_count'],
                        'sample_duration': atom['duration'],
                        'samples_per_sec': int(track_timescale / atom['duration']),
                        'duration': int((atom['sample_count'] * atom['duration'])/track_timescale)
                    }
                )
                track_duration -= atom['sample_count'] * atom['duration']

        return ret

    def get_chunk_count(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stco.entry_count

    def get_chunk_entry_count(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stsc.entry_count

    def get_chunk_info_arr(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stsc.chunk_info
    
    def get_chunk_offset_arr(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stco.chunk_offset_arr

    def get_sample_size_arr(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stsz.sample_size_arr

    def get_iframe_sample_index_arr(self):
        return self.moov.video_track.mida.minf.stbl.stsz.sample_size_arr

    def get_duration(self):
        return int(self.moov.video_track.tkhd.duration / self.moov.mvhd.timescale)

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
        
    # def get_sample_by_time(self, time_str, track='video_track'):
    #     """
    #     desc:
    #     시간 값에 맞는 sample을 가져옵니다.

    #     ret:
    #     sample_offset, sample_size, sample_timestamp
    #     """
    #     _time, _pow = 0, 0
    #     sample_arr = self.get_sample_arr(track)
    #     try:
    #         time_arr = [int(f) for f in time_str.split(':')]
    #     except ValueError as ve:
    #         logger.error('[get_chunk_by_time] : invalid time format')
    #         assert False
    #     time_arr.reverse()
    #     for t in time_arr:
    #         _time += pow(60, _pow) * t
    #     del time_arr

    #     duration = self.get_duration()
    #     if _time > duration:
    #         logger.error('[get_chunk_by_time] : invalid requested time')
    #         assert False
        
    #     samples_per_sec_arr = self.get_samples_per_sec_arr(track)
    #     sample_idx = 0
    #     cur_duration = 0
    #     remain_duration = _time
    #     for sample_count_per_sec in samples_per_sec_arr:
    #         if cur_duration > _time:
    #             logger.error('[get_chunk_by_time] : 뭔가 잘못되었다')
    #             assert False
    #         else:
    #             if remain_duration >= sample_count_per_sec['duration']:
    #                 remain_duration -= sample_count_per_sec['duration']
    #                 sample_idx += sample_count_per_sec['sample_count']
    #                 cur_duration += sample_count_per_sec['duration']
    #             else:
    #                 sample_idx += (sample_count_per_sec['samples_per_sec']*remain_duration)
    #                 cur_duration += remain_duration
    #                 break
    #     return sample_arr[sample_idx]['sample_offset'], sample_arr[sample_idx]['sample_size'], cur_duration

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

    def parse_ftype(self):
        ftyp_header = AtomBoxHeader.from_buffer(bytearray(self.binary))
        ftyp_bin = self.get_atombox_data(ftyp_header)
        self.ftype = AtomBox(ftyp_header, ftyp_bin)

    def parse_moov(self):
        assert self.ftype
        offset = self.ftype.header.size
        moov_header = AtomBoxHeader.from_buffer(bytearray(self.binary[offset:]))
        moov_bin = self.get_atombox_data(moov_header, offset)
        self.moov = MOOV(moov_header, moov_bin)

    def parse_header(self):
        self.parse_ftype()
        self.parse_moov()
        parser.make_chunk_arr()

    def parse_full(self):
        self.parse_header()
        self.mdat = self.binary[self.ftype.header.size + self.moov.header.size : ]

class MpegTool(object):
    def __init__(self) -> None:
        self.parser = MpegParser()
        pass

    def trim(self, src, start_timestamp, duration):
        """
        src : mp4 header가 포함된 binary
        start_timestamp : trim의 시작지점
        duration : trim한 동영상의 running time
        """
        self.parser.set_binary(src)
        self.parser.parse_header()
        chunk_i = self.parser.get_chunk_by_time(start_timestamp, 'video_track')
        
        # step1 > stts 수정
        # - 현재 chunk 앞에 몇 개의 sample이 있는지 확인 후, stts 헤더 수정
        # - 지워지는 sample 만큼 sample_count 삭제
        stts_info = self.parser.get_samples_per_sec_arr('video_track')
        removed_sample_count = chunk_i['start_sample_idx'] + 1
        for s in stts_info:
            if s['sample_count'] <= removed_sample_count:
                stts_info.pop(0)
                removed_sample_count -= s['sample_count']
            else:
                s['sample_count'] -= removed_sample_count

        # step2 > stsc 수정
        # - 현재 chunk 앞에 몇 개의 chunk가 있는지 확인 후, stsc 헤더 수정
        removed_chunk = chunk_i['chunk_idx']
        
        # 현재 chunk 앞에 몇 개의 sample이 있는지 확인 후, stts 헤더 수정
        # - 지워지는 sample 만큼 sample_count 삭제




if __name__ == '__main__':
    _bin = b''
    with open('./video_source/0-3.mp4', 'rb') as f:
        _bin = f.read()
    parser = MpegParser()
    parser.set_binary(_bin)
    parser.parse_full()
    chunk_arr = parser.chunk_arr['video_track']
    sample_arr = parser.sample_arr['video_track']
    print(parser.get_chunk_by_sample_index(74))
    pass