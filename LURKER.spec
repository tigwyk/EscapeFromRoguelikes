# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['EscapeFromRoguelikes\\main.py'],
             pathex=['C:\\Users\\Lee\\Documents\\GitHub\\EscapeFromRoguelikesProject\\env'],
             binaries=[],
             datas=[('./EscapeFromRoguelikes/audio/game_over.wav', 'audio'), ('./EscapeFromRoguelikes/audio/menu_lurker.wav', 'audio'), ('./EscapeFromRoguelikes/audio/med_medkit_offline_use.wav', 'audio/'), ('./EscapeFromRoguelikes/audio/new_game.wav', 'audio'), ('./EscapeFromRoguelikes/audio/stairs.mp3', 'audio'), ('./EscapeFromRoguelikes/audio/pistol_shot.wav', 'audio'), ('./EscapeFromRoguelikes/audio/shotgun_reload.wav', 'audio'), ('./EscapeFromRoguelikes/russian_names/_data.zip', 'russian_names'), ('./EscapeFromRoguelikes/img/dejavu10x10_gs_tc.png', 'img'), ('./EscapeFromRoguelikes/img/Taffer_10x10.png', 'img'), ('./EscapeFromRoguelikes/img/menu_background2.png', 'img'), ('./EscapeFromRoguelikes/audio/scav6_death_03.wav', 'audio'), ('./EscapeFromRoguelikes/README.md', '.')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='LURKER',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='LURKER')
