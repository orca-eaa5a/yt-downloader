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

    def get_sample_atom_arr(self, track='video_track'):
        return getattr(self.moov, track).mida.minf.stbl.stts.sample_atom_arr

    def get_sample_count(self, track='video_track'):
        count = 0
        for atom in self.get_sample_atom_arr(track):
            count += atom['sample_count']
        return count

    def get_sample_arr(self, track='video_track'):
        return self.sample_arr[track]

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

    def get_chunk_idx_from_sample_idx(self, sample_idx, track='video_track'):
        """
        sample_index를 기반으로, sample이 포함된 chunk를 가져옵니다.
        ! sample_index는 0부터 시작합니다.
        ! chunk_indexsms 1부터 시작합니다

        ret:
        chunk_index
        """
        chunk_info_arr = self.get_chunk_info_arr(track)
        if not chunk_info_arr:
            logging.error('[get_chunk_idx_from_sample_idx] fail to get chunk_info_arr')
            assert False
        prev_chunk_info = chunk_info_arr[0]
        for chunk_info in chunk_info_arr[1:]:
            sample_idx -= ((chunk_info['first_chunk'] - prev_chunk_info['first_chunk'])*prev_chunk_info['samples_per_chunk'])
            cur_chunk_sample_count = ((chunk_info['first_chunk'] - prev_chunk_info['first_chunk'])*prev_chunk_info['samples_per_chunk'])
            if cur_chunk_sample_count >= sample_idx:
                return chunk_info['first_chunk'] + int(sample_idx/chunk_info['samples_per_chunk'])
        
        return 1

    def get_chunk_by_sample_index(self, sample_index, track='video_track'):
        """
        sample_index를 기반으로, sample이 포함된 chunk를 가져옵니다.
        ! sample_index는 0부터 시작합니다.

        ret:
        chunk_index
        """
        return self.get_chunk_by_index(
            self.get_chunk_idx_from_sample_idx(sample_index, track), track
        )

    def get_chunk_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 chunk를 가져옵니다.
        ! index는 1부터 시작합니다

        ret:
        chunk_offset, chunk_size, sample_index, samples_per_chunk
        """
        sample_arr = self.get_sample_arr(track)
        chunk_info_arr = self.get_chunk_info_arr(track)
        chunk_offset_arr = self.get_chunk_offset_arr(track)

        i = 0
        j = 0
        while True:
            if chunk_info_arr[i]['first_chunk'] == sample_arr[j]['chunk_idx']:
                break
            else:
                j += chunk_info_arr[i]['samples_per_chunk']
                i += 1
                assert len(sample_arr) >= j
        k = j
        for sample in sample_arr[k:]:
            if sample['chunk_idx'] == index:
                break
            j += 1
        
        chunk_offset = chunk_offset_arr[index-1]
        chunk_size = 0
        sample_index = sample_arr[j]['sample_idx']
        samples_per_chunk = chunk_info_arr[i]['samples_per_chunk']

        for sample in sample_arr[j:]:
            if index != sample['chunk_idx']:
                break
            chunk_size += sample['sample_size']
        
        return chunk_offset, chunk_size, sample_index, samples_per_chunk

    def get_sample_by_time(self, time_str, track='video_track'):
        """
        desc:
        시간 값에 맞는 sample을 가져옵니다.

        ret:
        sample_offset, sample_size, sample_timestamp
        """
        _time, _pow = 0, 0
        sample_arr = self.get_sample_arr(track)
        try:
            time_arr = [int(f) for f in time_str.split(':')]
        except ValueError as ve:
            logger.error('[get_chunk_by_time] : invalid time format')
            assert False
        time_arr.reverse()
        for t in time_arr:
            _time += pow(60, _pow) * t
        del time_arr

        duration = self.get_duration()
        if _time > duration:
            logger.error('[get_chunk_by_time] : invalid requested time')
            assert False
        
        samples_per_sec_arr = self.get_samples_per_sec_arr(track)
        sample_idx = 0
        cur_duration = 0
        remain_duration = _time
        for sample_count_per_sec in samples_per_sec_arr:
            if cur_duration > _time:
                logger.error('[get_chunk_by_time] : 뭔가 잘못되었다')
                assert False
            else:
                if remain_duration >= sample_count_per_sec['duration']:
                    remain_duration -= sample_count_per_sec['duration']
                    sample_idx += sample_count_per_sec['sample_count']
                    cur_duration += sample_count_per_sec['duration']
                else:
                    sample_idx += (sample_count_per_sec['samples_per_sec']*remain_duration)
                    cur_duration += remain_duration
                    break
        return sample_arr[sample_idx]['sample_offset'], sample_arr[sample_idx]['sample_size'], cur_duration

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

        sample_offset, _, _ = self.get_sample_by_time(track)
        
        return self.get_chunk_by_offset(sample_offset, track)

    def get_chunk_by_offset(self, offset, track='video_track'):
        """
        desc:
        offset에 맞는 chunk를 가져옵니다.
        offset에 해당하는 sample이 chunk의 시작 sample이 아닐 경우,
        chunk의 시작 sample을 가져옵니다.

        ret:
        chunk_offset, chunk_size, samples
        """
        chunk_offset_arr = self.get_chunk_offset_arr(track)
        prev_offset = chunk_offset_arr[0]
        chunk_index = 1
        for chunk_offset in chunk_offset_arr[1:]:
            if prev_offset <= offset and offset < chunk_offset:
                return chunk_index
            chunk_index += 1
            prev_offset = chunk_offset
        
        return self.get_chunk_by_index(chunk_index, track)

    def get_sample_by_index(self, index, track='video_track'):
        """
        desc:
        index에 맞는 sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """
        sample_arr = self.get_sample_arr(track)
        sample = sample_arr[index]

        return sample['sample_offset'], sample['sample_size']

    def get_sample_by_offset(self, offset, track):
        """
        desc:
        offset에 맞는 sample을 가져옵니다.
        offset이 sample의 시작 지점이 아닐 경우, 범위 내에 offset을 포함하는
        sample을 가져옵니다.

        ret:
        sample_offset, sample_size
        """

        sample_arr = self.get_sample_arr(track)
        chunk_offset_arr = self.get_chunk_offset_arr(track)
        chunk_index = 1
        for chunk_offset in chunk_offset_arr:
            if chunk_offset <= offset:
                break
            chunk_index += 1
        
        _, _, sample_index, _ = self.get_chunk_by_index(chunk_index, track)
        _sample = None
        for sample in sample_arr[sample_index:]:
            if sample['sample_offset'] > offset:
                break
            _sample = sample
        return _sample['sample_offset'], _sample['sample_size']

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
        parser.make_sample_arr()

    def parse_full(self):
        self.parse_header()
        self.mdat = self.binary[self.ftype.header.size + self.moov.header.size : ]

class MpegTool(object):
    def __init__(self) -> None:
        self.parser = MpegParser()
        pass
    
    def merge(self, mp4_header, mp4_stream, stream_timestamp):
        """
        src : mp4 header가 포함된 binary
        dst : mp4 stream
        stream_timestamp : stream의 원래 시작 시간 정보
        mp4 binary 바로 뒤에 mp4 stream을 붙혀 연속적으로 재생될 수 있게 한다.
        1. stts 수정 필요
            - stream_timestamp와 sample_delta 기반으로 sample_count 수 조절 또는 배열 수정
        2. stsc 수정 필요
        3. stco 수정 필요
        4. stsz 수정 필요
        5. stss 수정 필요? <-- 확인 필요
        """
        self.parser.set_binary(mp4_header)
        self.parser.parse_header()
        o_chunk_offset, chunk_size, o_sample_index, samples_per_chunk = self.parser.get_chunk_by_time(stream_timestamp)
        

if __name__ == '__main__':
    _bin = b''
    with open('./video_source/0-3.mp4', 'rb') as f:
        _bin = f.read()
    parser = MpegParser()
    parser.set_binary(_bin)
    parser.parse()
    parser.get_chunk_by_time('2')
    pass