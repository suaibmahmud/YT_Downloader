import subprocess
import sys
import os
import yt_dlp

# yt_dlp লাইব্রেরির ভেতরের এক্সট্র্যাক্টর লোকেশন খুঁজে বের করা
yt_dlp_dir = os.path.dirname(yt_dlp.__file__)

# পাইইন্সটলারের জন্য বিল্ড কমান্ড কনফিগার করা
command = [
    sys.executable, "-m", "PyInstaller",
    "--noconsole",
    "--onefile",
    "--windowed",
    "--icon=icon.icns",
    f"--add-data={yt_dlp_dir}:yt_dlp", # yt-dlp এর সম্পূর্ণ ইন্টারনাল কোর ডেটা ফোল্ডারে পুশ করা
    "--collect-all", "imageio_ffmpeg",
    "--collect-all", "yt_dlp",
    "--copy-metadata", "yt-dlp",
    "--name=YT_Downloader",
    "main.py"
]

print("🚀 প্রফেশনাল ম্যাক অ্যাপ বিল্ড প্রসেস শুরু হচ্ছে...")
subprocess.run(command)
print("✅ বিল্ড সফল হয়েছে! 'dist/' ফোল্ডারটি চেক করুন।")
