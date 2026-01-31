#Install mutagen library
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import pandas as pd

#Song file
file = 'iphone.mp3'

#Reading metadata
audio = MP3(file, ID3=EasyID3)
duration = round(audio.info.length, 2)
title = audio.get('title', [''])[0]
artist = audio.get('artist', [''])[0]
album = audio.get('album', [''])[0]

df = pd.DataFrame([{
    'filename': file,
    'title': title,
    'artist': artist,
    'album': album,
    'duration (sec)': duration
}])
df.to_csv('horus_audio.csv', index=False)
print(df)
print("Audio to Horus file created")
