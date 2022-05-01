import time

import tcod.sdl.audio
import soundfile  # pip install soundfile

from pprint import pprint

class Sound:
    def __init__(self):
        # print("PySoundFile version:", soundfile.__version__)
        self.mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        self.load_sound_files()
        pass

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['mixer']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())

    def load_sound_files(self):
        self.soundFiles = {
        'reload':'audio/shotgun_reload.wav',
        'pistol_shot':'audio/pistol_shot.wav',
        'stairs' : 'audio/stairs.wav',
        'medkit' : 'audio/med_medkit_offline_use.wav',
        'game_over' : 'audio/game_over.wav',
        'new_game' : 'audio/new_game.wav',
        'death' : 'audio/scav6_death_03.wav',
        }

    def test_sound(self):
        print(f"Mixer: {vars(self.mixer)}")
        print(f'Mixer Device: {vars(self.mixer.device)}')
        sound, samplerate = soundfile.read(file="audio/menu_lurker.wav",dtype='float32')
        print(f"Sound ({sound}) Dtype ({sound.dtype}) Samplerate ({samplerate})")
        print(f"Available SoundFile formats: {soundfile.available_formats()}")

        sound = self.mixer.device.convert(sound, samplerate)  # Needed if dtype or samplerate differs.
        channel = self.mixer.play(sound)
        # while channel.busy:
        #     time.sleep(0.001)

    def play_music(self, music: str = "", volume: float = 0.1, loops: int = 0):
        menuFile = "audio/menu_lurker_remastered.wav"
        exploringFile = "audio/LURKER_Exploring.wav"
        overworldFile = "audio/LURKER_overworld_theme.wav"
        
        music_match = {
            "overworld_music": overworldFile,
            "exploring_music": exploringFile,
            "main_menu"      : menuFile,
        }
        
        try:
            sound, samplerate = self.read_audio_file(music_match[music])

            sound = self.mixer.device.convert(sound, samplerate)  # Needed if dtype or samplerate differs.
            channel = self.mixer.play(sound=sound, volume=volume, loops=loops)

            return channel
        except Exception as e:
            print(f"Audio error in play_music {e}")
            exit()

    def play_sound(self, soundId=None, volume: float = 0.2):
        if(soundId == None):
            return
        
        soundFile = self.soundFiles[soundId]
        try:
            sound, samplerate = self.read_audio_file(soundFile)
            sound = self.mixer.device.convert(sound, samplerate)  # Needed if dtype or samplerate differs.
            channel = self.mixer.play(sound=sound, volume=volume)
            return channel
        except Exception as e:
            print(f"Audio error in play_sound {e}")
            exit()
    
    def read_audio_file(self, filename):
        if(filename):
            signature, samplerate = soundfile.read(file=filename,dtype='float32')
            return signature, samplerate

