import os
import mutagen

directory = r"D:\Music\MusicBee\Music\anime"

# TODO: split into read, write - then parallelise
with open("seen.txt", "w", encoding="utf8") as f:
    for filename in os.scandir(directory):
        if filename.name.endswith(".mp3"):
            song = mutagen.File(filename.path)
            songName = filename.name.replace(".mp3", "")
            fileLine = songName + " | " + song['TALB'].text[0] + '\n'
            f.write(fileLine)
        elif filename.name.endswith(".flac"):
            song = mutagen.File(filename.path)
            songName = filename.name.replace(".flac", "")
            fileLine = songName + " | " + song['album'][0] + '\n'
            f.write(fileLine)
        else:
            raise UserWarning
