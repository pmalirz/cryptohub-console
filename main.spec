# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct

VSVersionInfo_data = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('CompanyName', 'Przemek Malirz'),
                    StringStruct('FileDescription', 'CryptoTaxPL - Polish Crypto Tax Calculator'),
                    StringStruct('FileVersion', '1.0.0'),
                    StringStruct('InternalName', 'cryptotaxpl'),
                    StringStruct('LegalCopyright', 'Copyright © 2025 Przemek Malirz'),
                    StringStruct('OriginalFilename', 'cryptotaxpl.exe'),
                    StringStruct('ProductName', 'CryptoTaxPL'),
                    StringStruct('ProductVersion', '1.0.0')
                ])
        ])
    ]
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('.env.example', '.')
    ],
    hiddenimports=[
        'colorama',
        'pandas',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cryptotaxpl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=VSVersionInfo_data,
    icon='icon.ico'  # Add this if you have an icon file
)