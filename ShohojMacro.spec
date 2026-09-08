# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:/Users/Polash/AppData/Roaming/Python/Python314/site-packages/customtkinter', 'customtkinter'), ('assets', 'assets')]
binaries = []
hiddenimports = ['PIL', 'PIL._tkinter_finder', 'pynput', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'cv2', 'numpy', 'customtkinter', 'openpyxl', 'shohoj_macro', 'shohoj_macro.ai', 'shohoj_macro.core', 'shohoj_macro.gui', 'shohoj_macro.utils']
tmp_ret = collect_all('shohoj_macro')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ShohojMacro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:/macro/assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ShohojMacro',
)
