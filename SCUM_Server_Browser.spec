# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SCUM Server Browser
Builds a self-contained executable for Windows and Linux
"""

a = Analysis(
    ['scum_tracker/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('scum_tracker/assets', 'scum_tracker/assets'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.sip',
        'requests',
        'sqlite3',
        'icmplib',
        'aiohttp',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SCUM_Server_Browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
