import os
import sys
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctkinter
from fake_useragent import UserAgent
import imageio_ffmpeg
import yt_dlp

# UI থিম সেটআপ
ctkinter.set_appearance_mode("System")  # লাইট বা ডার্ক মোড অটোমেটিক নিবে
ctkinter.set_default_color_theme("blue")  # থিম কালার


# 🍏 ম্যাক অ্যাপের জন্য FFmpeg-এর সঠিক পাথ খুঁজে বের করার ফাংশন
def get_safe_ffmpeg_path():
    try:
        # অ্যাপ যদি PyInstaller দিয়ে বিল্ড করা হয়, তবে তার ইন্টারনাল পাথ নিবে
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            # PyInstaller সাধারণত প্যাকেজগুলো এভাবে ভেতরে রাখে
            possible_path = os.path.join(base_path, 'imageio_ffmpeg', 'binaries')
            if os.path.exists(possible_path):
                for file in os.listdir(possible_path):
                    if file.startswith("ffmpeg"):
                        return os.path.join(possible_path, file)
        
        # ভিএস কোডে নরমাল রান করার সময় ডিফল্ট লাইব্রেরি পাথ নিবে
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg" # কোনো কারণে না পেলে গ্লোবাল সিস্টেম পাথ ট্রাই করবে


class YouTubeDownloaderApp(ctkinter.CTk):

    def __init__(self):
        super().__init__()

        # উইন্ডো কনফিগারেশন (রিসাইজেবল এবং রেসপন্সিভ)
        self.title("YouTube Downloader")
        self.geometry("700x550")
        self.minsize(600, 450)

        # গ্রিড লেআউট রেসপন্সিভ করার জন্য কনফিগারেশন
        self.grid_columnconfigure(0, weight=1)

        # ভ্যারিয়েবলস
        self.download_path = os.path.expanduser("~/Downloads")
        self.user_agent_rotator = UserAgent()

        # UI এলিমেন্ট তৈরি করা
        self.create_widgets()

    def create_widgets(self):
        # ১. টাইটেল লেবেল
        self.title_label = ctkinter.CTkLabel(
            self,
            text="YouTube Video & Audio Downloader",
            font=ctkinter.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=25, sticky="ew")

        # ২. ইউআরএল ইনপুট বক্স
        self.url_entry = ctkinter.CTkEntry(
            self,
            placeholder_text="Paste the YouTube video link here...",
            height=45,
        )
        self.url_entry.grid(row=1, column=0, padx=30, pady=10, sticky="ew")

        # ৩. ডেস্টিনেশন ফোল্ডার সিলেক্ট ফ্রেম
        self.path_frame = ctkinter.CTkFrame(self, fg_color="transparent")
        self.path_frame.grid(row=2, column=0, padx=30, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.path_label = ctkinter.CTkLabel(
            self, text=f"Preservation will take place: {self.download_path}", anchor="w"
        )
        self.path_label.grid(row=2, column=0, padx=35, pady=0, sticky="w")

        self.browse_btn = ctkinter.CTkButton(
            self.path_frame,
            text="Change the folder",
            command=self.browse_folder,
            width=150,
        )
        self.browse_btn.grid(row=0, column=1, padx=5, sticky="e")

        # ৪. অপশন ফ্রেম (টাইপ এবং কোয়ালিটি)
        self.option_frame = ctkinter.CTkFrame(self)
        self.option_frame.grid(row=3, column=0, padx=30, pady=20, sticky="ew")
        self.option_frame.grid_columnconfigure((0, 1), weight=1)

        self.type_label = ctkinter.CTkLabel(
            self.option_frame, text="Download type:"
        )
        self.type_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.type_combo = ctkinter.CTkComboBox(
            self.option_frame,
            values=["Video", "Audio Only"],
            command=self.update_quality_options,
        )
        self.type_combo.grid(row=0, column=0, padx=120, pady=10, sticky="ew")

        self.quality_label = ctkinter.CTkLabel(
            self.option_frame, text="Select quality:"
        )
        self.quality_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")

        self.quality_combo = ctkinter.CTkComboBox(
            self.option_frame, values=["Best Quality", "1080p", "720p", "480p"]
        )
        self.quality_combo.grid(row=0, column=1, padx=150, pady=10, sticky="ew")

        # 5. প্রোগ্রেস বার এবং স্ট্যাটাস
        self.progress_label = ctkinter.CTkLabel(self, text="", text_color="gray")
        self.progress_label.grid(row=4, column=0, padx=30, pady=5, sticky="ew")

        self.progress_bar = ctkinter.CTkProgressBar(self)
        self.progress_bar.grid(row=5, column=0, padx=30, pady=10, sticky="ew")
        self.progress_bar.set(0)

        # ৬. ডাউনলোড বাটন
        self.download_btn = ctkinter.CTkButton(
            self,
            text="Start the download",
            font=ctkinter.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#24a0ed",
            hover_color="#007cc7",
            command=self.start_download_thread,
        )
        self.download_btn.grid(row=6, column=0, padx=30, pady=25, sticky="ew")

    def browse_folder(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.download_path = selected_dir
            self.path_label.configure(text=f"Preservation will take place: {self.download_path}")

    def update_quality_options(self, choice):
        if "Audio" in choice:
            self.quality_combo.configure(values=["320kbps", "256kbps", "128kbps"])
            self.quality_combo.set("320kbps")
        else:
            self.quality_combo.configure(
                values=["Best Quality", "1080p", "720p", "480p"]
            )
            self.quality_combo.set("Best Quality")

    def progress_hook(self, d):
        if d["status"] == "downloading":
            # মোট ফাইলের সাইজ এবং ডাউনলোড হওয়া সাইজ বের করা
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            downloaded = d.get("downloaded_bytes", 0)
            percentage = downloaded / total
            self.progress_bar.set(percentage)

            # স্পিড এবং বাকি সময়ের স্ট্যাটাস আপডেট
            speed = d.get("_speed_str", "0B/s")
            eta = d.get("_eta_str", "00:00")
            self.progress_label.configure(
                text=f"Downloading... Speed: {speed} | বাকি সময়: {eta}"
            )
        elif d["status"] == "finished":
            self.progress_label.configure(
                text="Download complete! File is being processed..."
            )

    def start_download_thread(self):
        # UI হ্যাং হওয়া আটকাতে ব্যাকগ্রাউন্ড থ্রেডে ডাউনলোড চালানো
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please provide a valid link!")
            return

        self.download_btn.configure(state="disabled", text="Please wait...")
        threading.Thread(target=self.download_media, args=(url,), daemon=True).start()

    def download_media(self, url):
        download_type = self.type_combo.get()
        quality = self.quality_combo.get()

        # র্যান্ডম ব্রাউজার হেডার জেনারেশন (বট ট্র্যাকিং এড়াতে)
        random_user_agent = self.user_agent_rotator.random

        # 🚀 আলটিমেট সলিউশন: কোনো ব্রাউজার কুকি খোঁজা হবে না, ফলে আর কোনো 'Could not find cookies database' এরর আসবে না।
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
            'http_headers': {
                'User-Agent': random_user_agent,
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            
            # 📱 ইউটিউবের মোবাইল ও অ্যান্ড্রয়েড ক্লায়েন্ট ইমিটেশন 
            # এই সেটিংসটি ইউটিউবকে মনে করাবে এটি একটি আসল মোবাইল ডিভাইস, যা কুকি ছাড়াই ভিডিও ডাউনলোড করতে দেয়।
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android'],
                    'player_skip': ['webpage', 'configs']
                }
            }
        }

        # ফরম্যাট সিলেকশন লজিক (ভিডিও এবং অডিওর কোয়ালিটি নির্ধারণ)
        if "Audio" in download_type:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320' if '320' in quality else '192',
            }]
        else:
            if quality == "1080p":
                ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
            elif quality == "720p":
                ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
            elif quality == "480p":
                ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best'
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'

        # ডাউনলোড এক্সিকিউশন
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.progress_bar.set(1)
            self.progress_label.configure(text="The download has been completed successfully!")
            messagebox.showinfo("Success", "Your file has been downloaded successfully!")
        except Exception as e:
            self.progress_label.configure(text="Download failed.")
            messagebox.showerror("Download Error", f"A problem has occurred:\n{str(e)}")
        finally:
            self.download_btn.configure(state="normal", text="Start the download")



if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
