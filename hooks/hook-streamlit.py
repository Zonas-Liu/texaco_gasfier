from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# Streamlit 在运行时需要访问自身的 package metadata（version.py 会调用 importlib.metadata.version）
datas = copy_metadata("streamlit")

# Streamlit 前端静态资源（static/index.html 等）也必须被打包，否则访问根路径会 404
datas += collect_data_files("streamlit", includes=["static/**/*"])
