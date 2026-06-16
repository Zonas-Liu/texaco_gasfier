# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('app.py', '.'), ('src', 'src'), ('data', 'data')]
datas += collect_data_files('streamlit')

# 显式声明 Streamlit 运行时容易缺失的隐藏导入
# hooks/hook-streamlit.py 中已使用 collect_submodules('streamlit') 兜底
hiddenimports = [
    'streamlit.runtime.scriptrunner.magic_funcs',
    'streamlit.web.cli',
    'streamlit.web.bootstrap',
]

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['./hooks'],
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
    a.binaries,
    a.datas,
    [],
    name='TEXACO_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
