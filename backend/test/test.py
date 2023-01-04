import ssl
from pytube import YouTube
ssl._create_default_https_context = ssl._create_unverified_context

DOWNLOAD_DIR = r"./video"

# yt = YouTube('https://www.youtube.com/watch?v=UXJoXsMBCJg')
yt = YouTube('https://www.youtube.com/watch?v=UOgVzLU98jk')
stream = yt.streams.get_highest_resolution()

yt2 = YouTube('https://www.youtube.com/watch?v=2aN4D-IgBBg&t=1197s')
stream2 = yt.streams.get_highest_resolution()
# stream.download(DOWNLOAD_DIR)
pass
