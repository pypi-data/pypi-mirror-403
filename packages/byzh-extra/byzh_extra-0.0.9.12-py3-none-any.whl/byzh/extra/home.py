import os
import requests
import zipfile
from pathlib import Path
import shutil
from byzh.core import B_os

def env_all_ensure():
    env_home_ensure()
    env_ffmpeg_ensure()

def env_home_ensure():
    BYZH_HOME = os.getenv("BYZH_HOME", os.path.expanduser('~/.cache/byzh'))
    os.makedirs(BYZH_HOME, exist_ok=True)

def __download_file(url: str, save_path: str, chunk_size: int = 1024):
    """
    从 url 下载文件到指定路径

    :param url: 文件下载链接
    :param save_path: 保存路径 (包括文件名)
    :param chunk_size: 每次写入的块大小 (默认 1024 bytes)
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = downloaded * 100 / total_size
                        print(f"\rDownloading {percent:.2f}%...", end="")

    print(f"\n下载完成: {save_path}")

def env_ffmpeg_ensure():
    env_home_ensure()
    BYZH_HOME = os.getenv("BYZH_HOME", os.path.expanduser('~/.cache/byzh'))

    ffmpeg_exe_path = os.path.join(BYZH_HOME, 'ffmpeg.exe')
    if not os.path.exists(ffmpeg_exe_path):
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        __download_file(url, os.path.join(BYZH_HOME, "ffmpeg.zip"))
        with zipfile.ZipFile(os.path.join(BYZH_HOME, "ffmpeg.zip"), "r") as zip_ref:
            zip_ref.extractall(os.path.join(BYZH_HOME, "ffmpeg"))
        # 复制文件到指定目录
        shutil.copyfile(
            os.path.join(BYZH_HOME, "ffmpeg", "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe"),
            os.path.join(BYZH_HOME, 'ffmpeg.exe')
        )
        B_os.rm(os.path.join(BYZH_HOME, "ffmpeg"))
        B_os.rm(os.path.join(BYZH_HOME, "ffmpeg.zip"))

if __name__ == '__main__':
    env_ensure()