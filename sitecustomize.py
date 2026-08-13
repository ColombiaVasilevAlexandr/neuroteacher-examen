import os
import sys
import subprocess
import importlib

if os.environ.get('GITHUB_ACTIONS') == 'true' and 'pip' not in os.path.basename(sys.argv[0]).lower():
    try:
        import imageio_ffmpeg
    except Exception:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'imageio-ffmpeg'])
        importlib.invalidate_caches()
        import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    bindir = '/tmp/cosyvoice-bin'
    os.makedirs(bindir, exist_ok=True)
    link = os.path.join(bindir, 'ffmpeg')
    try:
        if os.path.lexists(link):
            os.remove(link)
        os.symlink(ffmpeg_exe, link)
    except OSError:
        pass

    github_path = os.environ.get('GITHUB_PATH')
    if github_path:
        with open(github_path, 'a', encoding='utf-8') as f:
            f.write(bindir + '\n')
