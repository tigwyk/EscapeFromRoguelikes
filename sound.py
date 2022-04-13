import time
import pyglet

# import tcod.sdl.audio

soundFiles = {
    'reload':'audio/shotgun_reload.wav',
    'pistol_shot':'audio/pistol_shot.wav',
    'stairs' : 'audio/stairs.mp3',
    'medkit' : 'audio/med_medkit_offline_use.wav',
    'game_over' : 'audio/game_over.wav',
    'new_game' : 'audio/new_game.wav',
    'death' : 'audio/scav6/scav6_death_03.wav',
    }
# mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
reload_sound = pyglet.media.StaticSource(pyglet.media.load(soundFiles['reload']))
pistol_shot_sound = pyglet.media.StaticSource(pyglet.media.load(soundFiles['pistol_shot']))
medkit_sound = pyglet.media.StaticSource(pyglet.media.load(soundFiles['medkit']))

stairs_sound = pyglet.media.load(soundFiles['stairs'])

new_game_sound = pyglet.media.load(soundFiles['new_game'])
game_over_sound = pyglet.media.load(soundFiles['game_over'])

death_sound = pyglet.media.load(soundFiles['death'])

soundMap = {
    'reload' : reload_sound,
    'pistol_shot' : pistol_shot_sound,
    'stairs' : stairs_sound,
    'medkit' : medkit_sound,
    'game_over' : game_over_sound,
    'new_game' : new_game_sound,
    'death' : death_sound
}

def init():
    pyglet.app.run()

def main_menu_music():
    # menu_player = pyglet.media.Player()
    soundFile = "audio/menu_lurker.wav"
    try:
        music = pyglet.media.load(filename=soundFile)
        # menu_player.volume = 0.5
        # menu_player.queue(music)
        
        menu_player = music.play()
        menu_player.volume = 0.02
        return menu_player
    except:
        print("Audio error in main_menu_music")
        exit()    

def play_sound(soundId=None):
    # player = pyglet.media.Player()
    if(soundId == None):
        return
    
    soundFile = soundMap[soundId]
    # try:
    #     # player.queue(reload_sound)
    #     soundMap[soundId].play()
    # except:
    #     print("Audio error in play_sound")
    #     exit()
    player = soundFile.play()
    player.volume = 0.1

