import ctypes
from io import BytesIO

class AtomBoxHeader(ctypes.BigEndianStructure):
    _fields_ = [
        ('size', ctypes.c_uint32),
        ('type', ctypes.c_char*4)
    ]

class AtomBox(object):
    def __init__(self, header:AtomBoxHeader, data:bytes) -> None:
        self.header = header
        self.data = data
        self.data_size = len(self.data)
        pass

class MVHD(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = None # 1byte
        self.flags = 0 # 3byte
        self.creation_time = None # 8byte | 4byte
        self.modification_time = None # 8byte | 4byte
        self.timescale = None # 8byte | 4byte
        self.duration = None # 8byte | 4byte
        self.reserved1 = 0x10000 # 4byte
        self.reserved2 = 0x100 # 2byte
        self.reserved3 = 0 # 2byte
        self.reserved4 = None # 4byte * 17
        self.next_track_id = None # 4byte
        self.parse_data()
    
    def parse_data(self):
        dyn_read_sz = 4
        data = BytesIO(self.data)
        self.version = int.from_bytes(data.read(1), byteorder="big")
        data.read(3) # flag
        if self.version == 1:
            dyn_read_sz = 8
        self.creation_time = data.read(dyn_read_sz)
        self.modification_time = data.read(dyn_read_sz)
        self.timescale = int.from_bytes(data.read(dyn_read_sz), byteorder="big")
        self.duration = int.from_bytes(data.read(dyn_read_sz), byteorder="big")
        self.next_track_id = int.from_bytes(self.data[:-4], byteorder="big")

class TKHD(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = None # 1byte
        self.flags = 1 # 3byte
        self.creation_time = None # 8byte | 4byte
        self.modification_time = None # 8byte | 4byte
        self.track_id = None
        self.duration = None
        self.width = None
        self.height = None
        self.parse_data()
    
    def parse_data(self):
        dyn_read_sz = 4
        data = BytesIO(self.data)
        self.version = int.from_bytes(data.read(1), byteorder="big")
        data.read(3) # flag
        if self.version == 1:
            dyn_read_sz = 8
        self.creation_time = data.read(dyn_read_sz)
        self.modification_time = data.read(dyn_read_sz)
        self.track_id = int.from_bytes(data.read(4), byteorder="big")
        data.read(4)
        self.duration = int.from_bytes(data.read(4), byteorder="big")
        self.width = int.from_bytes(self.data[-8:-6], byteorder="big")
        self.height = int.from_bytes(self.data[-4:-2], byteorder="big")

class MDHD(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = None
        self.flags = 0
        self.creation_time = None
        self.modification_time = None
        self.timescale = None
        self.duration = None
        self.parse_data()

    def parse_data(self):
        dyn_read_sz = 4
        data = BytesIO(self.data)
        self.version = int.from_bytes(data.read(1), byteorder="big")
        data.read(3) # flag
        if self.version == 1:
            dyn_read_sz = 8
        self.creation_time = data.read(dyn_read_sz)
        self.modification_time = data.read(dyn_read_sz)
        self.timescale = int.from_bytes(data.read(dyn_read_sz), byteorder="big")
        self.duration = int.from_bytes(data.read(dyn_read_sz), byteorder="big")

class HDLR(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.track_type = "sound"
        self.parse_data()

    def parse_data(self):
        data = BytesIO(self.data)
        data.read(1 + 3 + 4)
        if data.read(4) == b'vide':
            self.track_type = "video"

class STTS(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = 0
        self.flags = 0
        self.entry_count = 0
        self.sample_atom_arr = []
        self.parse_data()
        
    def parse_data(self):
        data = BytesIO(self.data[4:])
        self.entry_count = int.from_bytes(data.read(4), byteorder='big')
        for i in range(self.entry_count):
            self.sample_atom_arr.append(
                {
                    'sample_count': int.from_bytes(data.read(4), byteorder='big'),
                    'duration': int.from_bytes(data.read(4), byteorder='big')
                }
            )
        # logger.info('this parser not handle that len(self.sample_atom_arr) > 2')
        # logger.info('please report the sample or add the logic to parse that len(self.sample_atom_arr) > 2')
        # assert len(self.sample_atom_arr) < 2

class STSC(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = 0
        self.flags = 0
        self.entry_count = 0
        self.chunk_info = []
        self.parse_data()

    def parse_data(self):
        data = BytesIO(self.data[4:])
        self.entry_count = int.from_bytes(data.read(4), byteorder='big')
        for i in range(self.entry_count):
            self.chunk_info.append({
                'first_chunk': int.from_bytes(data.read(4), byteorder='big'),
                'samples_per_chunk': int.from_bytes(data.read(4), byteorder='big'),
                'sample_desc_index': int.from_bytes(data.read(4), byteorder='big'),
            })
        
class STCO(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = 0
        self.flags = 0
        self.entry_count = 0
        self.chunk_offset_arr = []
        self.parse_data()

    def parse_data(self):
        data = BytesIO(self.data[4:])
        self.entry_count = int.from_bytes(data.read(4), byteorder='big')
        for i in range(self.entry_count):
            self.chunk_offset_arr.append(
                int.from_bytes(data.read(4), byteorder='big')
            )
        pass

class STSZ(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = 0
        self.flags = 0
        self.sample_size = 0
        self.entry_count = 0
        self.sample_size_arr = []
        self.parse_data()
    
    def parse_data(self):
        data = BytesIO(self.data[8:])
        self.entry_count = int.from_bytes(data.read(4), byteorder='big')
        for i in range(self.entry_count):
            self.sample_size_arr.append(
                int.from_bytes(data.read(4), byteorder='big')
            )
        pass

class STSS(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.version = 0
        self.flags = 0
        self.entry_count = 0
        self.iframe_sample_index = []
        self.parse_data()
    
    def parse_data(self):
        data = BytesIO(self.data[4:])
        self.entry_count = int.from_bytes(data.read(4), byteorder='big')
        for i in range(self.entry_count):
            self.iframe_sample_index.append(
                int.from_bytes(data.read(4), byteorder='big')
            )
        pass

class STBL(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.stts = None
        self.stsc = None
        self.stco = None
        self.stsz = None
        self.stss = None
        self.parse_data()

    def parse_data(self):
        data = BytesIO(self.data)
        while True:
            box_header_bin = data.read(8)
            if not box_header_bin:
                break
            header = AtomBoxHeader.from_buffer(bytearray(box_header_bin))
            inner_data = data.read(header.size - ctypes.sizeof(AtomBoxHeader))
            if header.type == b'stts':
                self.stts = STTS(header, inner_data)
            elif header.type == b'stsc':
                self.stsc = STSC(header, inner_data)
            elif header.type == b'stco':
                self.stco = STCO(header, inner_data)
            elif header.type == b'stsz':
                self.stsz = STSZ(header, inner_data)
            elif header.type == b'stss':
                self.stss = STSS(header, inner_data)
            else:
                pass

class MINF(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.stbl = None
        self.parse_data()

    def parse_data(self):
        data = BytesIO(self.data)
        while True:
            box_header_bin = data.read(8)
            if not box_header_bin:
                break
            header = AtomBoxHeader.from_buffer(bytearray(box_header_bin))
            inner_data = data.read(header.size - ctypes.sizeof(AtomBoxHeader))
            if header.type == b'stbl':
                self.stbl = STBL(header, inner_data)
                pass
            else:
                pass

class MDIA(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.mdhd = None
        self.hdlr = None
        self.minf = None
        self.parse_data()
    
    def parse_data(self):
        data = BytesIO(self.data)
        while True:
            box_header_bin = data.read(8)
            if not box_header_bin:
                break
            header = AtomBoxHeader.from_buffer(bytearray(box_header_bin))
            inner_data = data.read(header.size - ctypes.sizeof(AtomBoxHeader))
            if header.type == b'mdhd':
                self.mdhd = MDHD(header, inner_data)
                pass
            elif header.type == b'hdlr':
                self.hdlr = HDLR(header, inner_data)
                pass
            elif header.type == b'minf':
                self.minf = MINF(header, inner_data)
                pass
            else:
                pass

class Track(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.tkhd = None
        self.mida = None
        self.parse_data()
    
    def parse_data(self):
        # parse tkhd
        data = BytesIO(self.data)
        while True:
            box_header_bin = data.read(8)
            if not box_header_bin:
                break
            header = AtomBoxHeader.from_buffer(bytearray(box_header_bin))
            inner_data = data.read(header.size - ctypes.sizeof(AtomBoxHeader))
            if header.type == b'mdia':
                self.mida = MDIA(header, inner_data)
                pass
            elif header.type == b'tkhd':
                self.tkhd = TKHD(header, inner_data)
            else:
                # not parse
                pass
        
class MOOV(AtomBox):
    def __init__(self, header: AtomBoxHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.mvhd = None
        self.video_track = None
        self.sound_track = None
        self.udta = None
        self.parse_data()
    
    def parse_data(self):
        data = BytesIO(self.data)
        while True:
            box_header_bin = data.read(8)
            if not box_header_bin:
                break
            header = AtomBoxHeader.from_buffer(bytearray(box_header_bin))
            inner_data = data.read(header.size - ctypes.sizeof(AtomBoxHeader))
            if header.type == b'mvhd':
                # parse mvhd
                self.mvhd = MVHD(header, inner_data)
                pass
            elif header.type == b'trak':
                # parse trak
                track = Track(header, inner_data)
                if track.mida.hdlr.track_type == 'video':
                    self.video_track = track
                elif track.mida.hdlr.track_type == 'sound':
                    self.sound_track = track
                else:
                    assert 0
                pass
            else:
                # not parse
                pass