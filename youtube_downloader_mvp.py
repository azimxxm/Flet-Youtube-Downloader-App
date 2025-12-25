import flet as ft
import yt_dlp
import os
import subprocess
import sys
from pathlib import Path
import threading
from ui_components import ProgressControl, RadioOptionComponent
from utils import metadata_cache, format_bytes, validate_youtube_url, check_ffmpeg_installed, get_responsive_dimensions

class YouTubeDownloaderMVP:
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.page.title = "YouTube Downloader - Simple"

        # Set responsive dimensions based on screen size
        width, height = get_responsive_dimensions(page)
        self.page.window_width = width
        self.page.window_height = height
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#1a1a1a"
        self.page.padding = 0
        
        # Custom Fonts
        self.page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Inter")

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # FilePicker for folder selection
        self.file_picker = ft.FilePicker()
        self.file_picker.on_result = self.on_folder_selected
        self.page.dialog = self.file_picker

        # Keyboard shortcuts
        self.page.on_keyboard_event = self.on_keyboard

        self.init_ui()

    def init_ui(self):
        # Header
        header_content = [
            ft.Icon(ft.Icons.BOLT, size=40, color=ft.Colors.YELLOW_ACCENT),
            ft.Text("Simple Downloader", size=24, weight=ft.FontWeight.BOLD, color="white"),
        ]
        
        if self.on_back:
            header_content.insert(0, ft.IconButton(
                icon=ft.Icons.ARROW_BACK, 
                icon_color="white",
                on_click=self.on_back,
                tooltip="Back to Menu"
            ))

        self.header = ft.Container(
            content=ft.Row(
                header_content,
                alignment=ft.MainAxisAlignment.CENTER if not self.on_back else ft.MainAxisAlignment.START,
            ),
            padding=ft.Padding.only(top=40, bottom=20, left=20),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=["#2d2d2d", "#1a1a1a"],
            ),
        )

        # Input Field
        self.url_field = ft.TextField(
            label="YouTube URL",
            hint_text="Paste video link here...",
            width=500,
            border_radius=10,
            bgcolor="#2d2d2d",
            border_color="#404040",
            focused_border_color=ft.Colors.YELLOW_ACCENT,
            text_style=ft.TextStyle(color="white"),
            label_style=ft.TextStyle(color="#aaaaaa"),
            prefix_icon=ft.Icons.LINK,
        )

        # Download Mode
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                RadioOptionComponent("Video (MP4)", "video", ft.Icons.VIDEOCAM, ft.Colors.YELLOW_ACCENT),
                RadioOptionComponent("Audio (MP3)", "audio", ft.Icons.AUDIOTRACK, ft.Colors.YELLOW_ACCENT),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            value="video"
        )

        # Location
        self.location_text = ft.Text(self.download_path, size=12, color="#888888", italic=True)
        self.location_container = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=16, color="#888888"),
                self.location_text,
                ft.TextButton("Change", on_click=self.open_file_picker, style=ft.ButtonStyle(color=ft.Colors.YELLOW_ACCENT))
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
        )

        # Progress Control
        self.progress_control = ProgressControl(width=500, page=self.page)

        self.download_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, color="black"),
                ft.Text("Download Now", color="black"),
            ], spacing=10),
            on_click=self.download_video,
            width=250,
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.YELLOW_ACCENT, "hovered": ft.Colors.YELLOW_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
        )

        self.downloaded_file_path = None

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        self.header,
                        ft.Container(
                            content=ft.Column([
                                self.url_field,
                                ft.Container(height=10),
                                self.download_mode,
                                self.location_container,
                                ft.Container(height=20),
                                self.download_btn,
                                ft.Container(height=20),
                                self.progress_control,
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            padding=30,
                            expand=True,
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                bgcolor="#1a1a1a",
                expand=True,
            )
        )

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_path = e.path
            self.location_text.value = e.path
            self.page.update()

    def open_file_picker(self, e):
        """Open file picker dialog"""
        self.page.dialog = self.file_picker
        self.file_picker.get_directory_path()

    def download_video(self, e):
        url = self.url_field.value.strip()

        if not url:
            self.url_field.error_text = "Please enter a URL"
            self.page.update()
            return

        # Validate YouTube URL
        is_valid, error_msg = validate_youtube_url(url)
        if not is_valid:
            self.url_field.error_text = error_msg
            self.url_field.border_color = ft.Colors.RED_ACCENT
            self.page.update()
            return

        # Check FFmpeg installation
        ffmpeg_ok, ffmpeg_error = check_ffmpeg_installed()
        if not ffmpeg_ok:
            self.progress_control.error(ffmpeg_error)
            self.page.update()
            return

        self.url_field.error_text = None
        self.download_btn.disabled = True
        self.progress_control.start_download()
        self.page.update()

        def download_thread():
            try:
                # Check if Audio or Video mode
                if self.download_mode.value == "audio":
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [self.progress_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'quiet': True,
                        'no_warnings': True,
                    }
                else:
                    ydl_opts = {
                        'format': 'bestvideo[vcodec=h264][ext=mp4]+bestaudio[acodec=aac][ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [self.progress_hook],
                        'merge_output_format': 'mp4',
                        'postprocessors': [{
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': 'mp4',
                        }],
                        'quiet': True,
                        'no_warnings': True,
                    }

                # Check cache first to avoid duplicate extract_info call
                cached_info = metadata_cache.get(url)
                if cached_info:
                    info = cached_info
                else:
                    # Fetch metadata with minimal options
                    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                    metadata_cache.set(url, info)

                # Now download using the fetched/cached info
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    filename = ydl.prepare_filename(info)

                    # For audio, filename will have .mp3 extension
                    if self.download_mode.value == "audio":
                        filename = filename.rsplit('.', 1)[0] + '.mp3'

                    # Use process_ie_result to download without re-fetching metadata
                    ydl.process_ie_result(info, download=True)
                    self.downloaded_file_path = filename

                mode_text = "Audio" if self.download_mode.value == "audio" else "Video"
                self.progress_control.complete(
                    f"✅ {mode_text} downloaded successfully!",
                    on_show_click=self.show_file
                )

            except Exception as ex:
                from utils import translate_error
                user_msg = translate_error(ex)
                self.progress_control.error(user_msg)

            finally:
                self.download_btn.disabled = False
                self.page.update()

        threading.Thread(target=download_thread, daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent = 0
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    percent = d['downloaded_bytes'] / d['total_bytes']
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    percent = d['downloaded_bytes'] / d['total_bytes_estimate']

                if percent > 0:
                    self.progress_control.update_progress(percent)
            except Exception:
                pass
        elif d['status'] == 'finished':
            # Capture actual filename from yt-dlp
            if 'filename' in d:
                self.downloaded_file_path = d['filename']

    def show_file(self, _e):
        if self.downloaded_file_path and os.path.exists(self.downloaded_file_path):
            subprocess.run(['open', '-R', self.downloaded_file_path])

    def on_keyboard(self, e: ft.KeyboardEvent):
        import platform
        ctrl = e.ctrl or (e.meta and platform.system() == "Darwin")

        if e.key == "Escape":
            if self.on_back:
                self.on_back(None)
        elif ctrl and e.key.lower() == "v":
            # Paste URL from clipboard
            try:
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                self.url_field.value = result.stdout.strip()
                self.page.update()
            except Exception:
                pass
        elif ctrl and e.key.lower() == "d":
            # Start download
            self.download_video(None)
        elif ctrl and e.key.lower() == "t":
            # Toggle theme
            from ui_components import ThemeManager
            ThemeManager.toggle_theme(self.page)


def main(page: ft.Page):
    YouTubeDownloaderMVP(page)


if __name__ == "__main__":
    ft.run(main)
