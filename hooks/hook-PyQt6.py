"""
PyInstaller hook for PyQt6
Ensures all PyQt6 modules and dependencies are properly bundled
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect everything from PyQt6
datas, binaries, hiddenimports = collect_all('PyQt6')

# Ensure all PyQt6 submodules are included
hiddenimports += collect_submodules('PyQt6')
