from mutagen import File
import os

def audio_to_horus(filename):
    try:
        audio = File(filename)
        if not audio:
            print("Unsupported or invalid audio format.")
            return
        print(f"filename: {os.path.basename(filename)}")
        if audio.info:
            if hasattr(audio.info, 'length'):
                print(f"duration (sec): {round(audio.info.length, 2)}")
            if hasattr(audio.info, 'bitrate'):
                print(f"bitrate: {audio.info.bitrate}")
            if hasattr(audio.info, 'sample_rate'):
                print(f"sample_rate: {audio.info.sample_rate}")
            if hasattr(audio.info, 'channels'):
                print(f"channels: {audio.info.channels}")

    except Exception as e:
        print("An error occurred:", str(e))
audio_to_horus("audio.mp3")
