# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for SyncFrame (Standalone Single-File ELF)."""

import os
import sys

block_cipher = None

# Exclude unnecessary Qt bindings and unused heavy modules to minimize binary size
# and accelerate startup time on Nobara / Linux environments.
excluded_modules = [
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DExtras',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtMultimediaQuick',
    'PySide6.QtTest',
    'PySide6.QtSql',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtPositioning',
    'PySide6.QtLocation',
    'PySide6.QtBluetooth',
    'PySide6.QtNfc',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml',
    'PySide6.QtCharts',
    'PySide6.QtDataVisualization',
    'PySide6.QtVirtualKeyboard',
    'unittest',
    'tkinter',
    'matplotlib',
    'PIL',
    'IPython',
]

# Bundle FlexiBLAS backends if present on the host system
flexiblas_binaries = []
for p in ['/usr/lib64/flexiblas', '/usr/lib/x86_64-linux-gnu/flexiblas', '/usr/lib/flexiblas']:
    if os.path.isdir(p):
        for f in os.listdir(p):
            if f.endswith('.so') or '.so.' in f:
                flexiblas_binaries.append((os.path.join(p, f), 'flexiblas'))
        break

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=flexiblas_binaries,
    datas=[],
    hiddenimports=[
        'src.ui.components.completion_dialog',
        'src.ui.components.audio_preserve_checkbox',
        'src.ui.components.collapsible_section',
        'src.ui.workers.unified_pipeline_worker',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SyncFrame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
