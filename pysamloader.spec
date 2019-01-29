# -*- mode: python -*-

import os
import platform
import PyInstaller.config

target = 'binary-{0}'.format(platform.system().lower())

workpath = os.path.join(os.getcwd(), 'build', target)
if not os.path.exists(workpath):
    os.makedirs(workpath)
PyInstaller.config.CONF['workpath'] = workpath

distpath = os.path.join(os.getcwd(), 'dist', target)
if not os.path.exists(distpath):
    os.makedirs(distpath)
PyInstaller.config.CONF['distpath'] = distpath

block_cipher = None

a = Analysis(['run.py'],
             pathex=[os.path.split(SPECPATH)[0]],
             binaries=[],
             datas=[],
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
