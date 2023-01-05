from pymp4.parser import Box
from io import BytesIO

with open('./video_source/0-3.mp4', 'rb') as f:
    _bin = f.read()

ftype = Box.parse(_bin)
moov = Box.parse(_bin[ftype.end:])
print(ftype)
print(moov)

