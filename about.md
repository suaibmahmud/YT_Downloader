# Need for this project

brew install ffmpeg

brew install python-tk

pip install imageio-ffmpeg

python3 -m venv venv

source venv/bin/activate

pip install customtkinter yt-dlp pillow requests fake-useragent pyinstaller

pyinstaller --noconsole --onefile --windowed --icon=icon.icns --name="YT_Downloader" main.py