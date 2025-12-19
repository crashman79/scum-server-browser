# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SCUM Server Browser
Builds a self-contained executable for Windows and Linux
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all PyQt6 components (Python bindings)
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all('PyQt6')

# Collect Qt libraries (DLLs on Windows, .so on Linux)
try:
    qt6_datas, qt6_binaries, qt6_hiddenimports = collect_all('PyQt6.Qt6')
except:
    qt6_datas, qt6_binaries, qt6_hiddenimports = [], [], []

# Collect SIP bindings
try:
    sip_datas, sip_binaries, sip_hiddenimports = collect_all('PyQt6.sip')
except:
    sip_datas, sip_binaries, sip_hiddenimports = [], [], []

a = Analysis(
    ['scum_tracker/__main__.py'],
    pathex=[],
    binaries=pyqt6_binaries + qt6_binaries + sip_binaries,
    datas=[
        ('scum_tracker/assets', 'scum_tracker/assets'),
    ] + pyqt6_datas + qt6_datas + sip_datas,
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
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'scipy',
        'scipy.interpolate',
        'numpy',
    ] + pyqt6_hiddenimports + qt6_hiddenimports + sip_hiddenimports + collect_submodules('PyQt6'),
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
