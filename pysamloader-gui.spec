# -*- mode: python -*-

import os
import platform
import PyInstaller.config
from kivy.deps import sdl2, glew

# Configure paths
target = 'binary-{0}'.format(platform.system().lower())

workpath = os.path.join(os.getcwd(), 'build', target)
if not os.path.exists(workpath):
    os.makedirs(workpath)
PyInstaller.config.CONF['workpath'] = workpath

distpath = os.path.join(os.getcwd(), 'dist', target)
if not os.path.exists(distpath):
    os.makedirs(distpath)
PyInstaller.config.CONF['distpath'] = distpath

# Build
block_cipher = None

a = Analysis(['rungui.py'],
             pathex=[os.path.split(SPECPATH)[0]],
             binaries=[],
             datas=[
                ('pysamloader/assets/binary.png', 'pyinstaller/assets/binary.png'),
                ('pysamloader/assets/connectors.png', 'pyinstaller/assets/connectors.png'),
                ('pysamloader/assets/finish.png', 'pyinstaller/assets/finish.png'),
                ('pysamloader/assets/info.png', 'pyinstaller/assets/info.png'),
                ('pysamloader/assets/logo-full.png', 'pyinstaller/assets/logo-full.png'),
                ('pysamloader/assets/sam-ic.png', 'pyinstaller/assets/sam-ic.png'),
                ('pysamloader/assets/verify.png', 'pyinstaller/assets/verify.png'),
                ('pysamloader/assets/write.png', 'pyinstaller/assets/write.png'),
             ],
             hiddenimports=[],
             hookspath=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='pysamloader',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
