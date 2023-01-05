from pymp4.parser import Box
from pymp4.util import BoxUtil
from io import BytesIO

with open('./video_source/0-3.mp4', 'rb') as f:
    _bin = f.read()

def box_find(box, ty):

    if box.type == ty:
        return box
    elif hasattr(box, "children"):
        return box_find(box, ty)
    else:
        assert 0

ftype = Box.parse(_bin)
moov = Box.parse(_bin[ftype.end:])
track = BoxUtil.first(moov, b'trak')
stsc = BoxUtil.first(track, b'stsc')
#track_list = BoxUtil.first(moov, b'trak')
print(stsc)

