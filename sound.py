import time

import pyglet

import tcod.sdl.audio
import soundfile  # pip install soundfile

class Sound:
    def __init__(self):
        # pyglet.app.run()
        # self.load_sound_files()
        pass

    def load_sound_files(self):
        self.soundFiles = {
        'reload':'audio/shotgun_reload.wav',
        'pistol_shot':'audio/pistol_shot.wav',
        'stairs' : 'audio/stairs.mp3',
        'medkit' : 'audio/med_medkit_offline_use.wav',
        'game_over' : 'audio/game_over.wav',
        'new_game' : 'audio/new_game.wav',
        'death' : 'audio/scav6_death_03.wav',
        }
        # mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        self.reload_sound = pyglet.media.StaticSource(pyglet.media.load(self.soundFiles['reload']))
        self.pistol_shot_sound = pyglet.media.StaticSource(pyglet.media.load(self.soundFiles['pistol_shot']))
        self.medkit_sound = pyglet.media.StaticSource(pyglet.media.load(self.soundFiles['medkit']))

        self.stairs_sound = pyglet.media.load(self.soundFiles['stairs'])

        self.new_game_sound = pyglet.media.load(self.soundFiles['new_game'])
        self.game_over_sound = pyglet.media.load(self.soundFiles['game_over'])

        self.death_sound = pyglet.media.load(self.soundFiles['death'])

        self.soundMap = {
            'reload' : self.reload_sound,
            'pistol_shot' : self.pistol_shot_sound,
            'stairs' : self.stairs_sound,
            'medkit' : self.medkit_sound,
            'game_over' : self.game_over_sound,
            'new_game' : self.new_game_sound,
            'death' : self.death_sound
        }

    def test_sound(self):
        mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        print(f"Mixer: {mixer}")
        sound, samplerate = soundfile.read("audio/shotgun_reload.wav")
        print(f"Sound ({sound}) Samplerate ({samplerate})")
        soundfile.write('audio/new_file.flac', sound, samplerate)
        # sound = mixer.device.convert(sound, samplerate)  # Needed if dtype or samplerate differs.
        # channel = mixer.play(sound)
        # while channel.busy:
        #     time.sleep(0.001)

    def play_music(self, music: str = ""):
        # menu_player = pyglet.media.Player()
        menuFile = "audio/menu_lurker.wav"
        exploringFile = "audio/LURKER_Exploring.mp3"
        overworldFile = "audio/LURKER_overworld_theme.mp3"
        
        music_match = {
            "overworld_music": overworldFile,
            "exploring_music": exploringFile,
            "main_menu"      : menuFile,
        }
        
        try:
            music = pyglet.media.load(filename=music_match[music])
            # menu_player.volume = 0.5
            # menu_player.queue(music)
            
            menu_player = music.play()
            menu_player.volume = 0.04
            return menu_player
        except Exception as e:
            print(f"Audio error in play_music {e}")
            exit()

    def exploring_music(self):
        # menu_player = pyglet.media.Player()
        soundFile = "audio/LURKER_Exploring.mp3"
        try:
            music = pyglet.media.load(filename=soundFile)
            # menu_player.volume = 0.5
            # menu_player.queue(music)
            
            player = music.play()
            player.volume = 0.04
            return player
        except Exception as e:
            print(f"Audio error in exploring_music {e}")
            exit()    
        
    def overworld_music(self):
        # menu_player = pyglet.media.Player()
        soundFile = "audio/LURKER_overworld_theme.mp3"
        try:
            music = pyglet.media.load(filename=soundFile)
            # menu_player.volume = 0.5
            # menu_player.queue(music)
            
            player = music.play()
            player.volume = 0.04
            return player
        except Exception as e:
            print(f"Audio error in exploring_music {e}")
            exit()    

    def play_sound(self, soundId=None):
        # player = pyglet.media.Player()
        if(soundId == None):
            return
        
        soundFile = self.soundMap[soundId]
        # try:
        #     # player.queue(reload_sound)
        #     soundMap[soundId].play()
        # except:
        #     print("Audio error in play_sound")
        #     exit()
        player = soundFile.play()
        player.volume = 0.1

