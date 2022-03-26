import time
import soundfile  # pip install soundfile
import tcod.sdl.audio

mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())

def main_menu_music():
    sound, samplerate = soundfile.read("./audio/menu_lurker.wav")
    sound = mixer.device.convert(sound, samplerate)  # Needed if dtype or samplerate differs.
    channel = mixer.play(sound)
    while channel.busy:
        time.sleep(0.001)