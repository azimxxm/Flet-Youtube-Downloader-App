import flet as ft
import yt_dlp
import os
import subprocess
from pathlib import Path
import threading
import time
from ui_components import ProgressControl

class YouTubeDownloaderAdvanced:
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.page.title = "YouTube Downloader"
        self.page.window_width = 800
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = "#1a1a1a"
        
        # Custom Fonts
        self.page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Inter")

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # FilePicker
        self.file_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.file_picker)

        self.formats_data = []
        self.init_ui()

    def init_ui(self):
        # Header
        header_content = [
            ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, size=40, color=ft.Colors.RED_ACCENT),
            ft.Text("YouTube Downloader", size=24, weight=ft.FontWeight.BOLD, color="white"),
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
            padding=ft.padding.only(top=40, bottom=20, left=20),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#2d2d2d", "#1a1a1a"],
            ),
        )

        # Input Section
        self.url_field = ft.TextField(
            label="YouTube Video URL",
            hint_text="Paste your link here...",
            width=500,
            border_radius=10,
            bgcolor="#2d2d2d",
            border_color="#404040",
            focused_border_color=ft.Colors.RED_ACCENT,
            text_style=ft.TextStyle(color="white"),
            label_style=ft.TextStyle(color="#aaaaaa"),
            prefix_icon=ft.Icons.LINK,
        )

        self.fetch_btn = ft.ElevatedButton(
            text="Analyze Video",
            icon=ft.Icons.SEARCH,
            style=ft.ButtonStyle(
                color="white",
                bgcolor={"": ft.Colors.RED_ACCENT, "hovered": ft.Colors.RED_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
            width=180,
            on_click=self.fetch_formats,
        )

        # Mode Selection
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                self.create_radio_option("Video (MP4)", "video", ft.Icons.VIDEOCAM),
                self.create_radio_option("Audio (MP3)", "audio", ft.Icons.AUDIOTRACK),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            value="video",
            on_change=self.on_mode_change
        )

        # Location Section
        self.location_text = ft.Text(self.download_path, size=12, color="#888888", italic=True)
        self.location_container = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=16, color="#888888"),
                self.location_text,
                ft.TextButton("Change", on_click=lambda _: self.file_picker.get_directory_path(), style=ft.ButtonStyle(color=ft.Colors.RED_ACCENT))
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
        )

        # Video Info Card (Hidden initially)
        self.video_info_card = ft.Container(
            visible=False,
            padding=20,
            bgcolor="#252525",
            border_radius=15,
            border=ft.border.all(1, "#333333"),
            animate_opacity=300,
            content=ft.Column([
                ft.Text("Video Details", size=16, weight=ft.FontWeight.BOLD, color="#aaaaaa"),
                ft.Divider(color="#333333"),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VIDEO_LIBRARY, color=ft.Colors.RED_ACCENT),
                        ft.Column([
                            ft.Text("Unknown Title", ref=self.bind_ref("video_title"), weight=ft.FontWeight.BOLD, size=16),
                            ft.Text("00:00", ref=self.bind_ref("video_duration"), size=12, color="#888888"),
                        ], spacing=2)
                    ]),
                    padding=10
                ),
                ft.Divider(color="#333333"),
                
                # Options
                ft.Row([
                    ft.Dropdown(
                        ref=self.bind_ref("format_dropdown"),
                        label="Quality",
                        width=200,
                        border_radius=10,
                        bgcolor="#333333",
                        border_color="#444444",
                    ),
                    ft.Checkbox(
                        ref=self.bind_ref("subtitle_checkbox"),
                        label="Subtitles",
                        value=False,
                        on_change=self.on_subtitle_change,
                        fill_color=ft.Colors.RED_ACCENT,
                    ),
                    ft.Dropdown(
                        ref=self.bind_ref("subtitle_lang_dropdown"),
                        label="Language",
                        width=120,
                        visible=False,
                        border_radius=10,
                        bgcolor="#333333",
                        options=[
                            ft.dropdown.Option("en", "English"),
                            ft.dropdown.Option("ru", "Russian"),
                            ft.dropdown.Option("uz", "Uzbek"),
                        ]
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                ft.ElevatedButton(
                    ref=self.bind_ref("download_btn"),
                    text="Download Now",
                    icon=ft.Icons.DOWNLOAD,
                    width=600, # Full width
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor={"": ft.Colors.GREEN_600, "hovered": ft.Colors.GREEN_700},
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=20,
                    ),
                    on_click=self.download_video
                )
            ])
        )

        # Progress Control
        self.progress_control = ProgressControl(width=600)
        self.progress_control.progress_bar.color = ft.Colors.RED_ACCENT

        # Main Layout
        self.page.add(
            ft.Column(
                [
                    self.header,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Paste a YouTube link to get started", size=14, color="#888888"),
                            ft.Row([self.url_field, self.fetch_btn], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=10),
                            self.download_mode,
                            self.location_container,
                            ft.Container(height=20),
                            self.video_info_card,
                            ft.Container(height=20),
                            self.progress_control,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=30,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        
        # Refs storage initialized in bind_ref

    def bind_ref(self, name):
        # A simple way to keep references to controls created inside containers
        if not hasattr(self, "refs"): self.refs = {}
        self.refs[name] = ft.Ref()
        return self.refs[name]

    def get_control(self, name):
        return self.refs[name].current

    def create_radio_option(self, label, value, icon):
        return ft.Container(
            content=ft.Row([
                ft.Radio(value=value, fill_color=ft.Colors.RED_ACCENT),
                ft.Icon(icon, size=20, color="white"),
                ft.Text(label, color="white")
            ]),
            bgcolor="#252525",
            padding=10,
            border_radius=10,
            border=ft.border.all(1, "#333333")
        )

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_path = e.path
            self.location_text.value = e.path
            self.page.update()

    def on_mode_change(self, e):
        # Hide video info if mode changes, forcing re-fetch or just reset UI
        self.video_info_card.visible = False
        self.progress_control.reset()
        self.page.update()

    def on_subtitle_change(self, e):
        lang_dropdown = self.get_control("subtitle_lang_dropdown")
        lang_dropdown.visible = e.control.value
        self.page.update()

    def fetch_formats(self, e):
        url = self.url_field.value.strip()
        if not url:
            self.url_field.error_text = "Please enter a URL"
            self.page.update()
            return
        
        self.url_field.error_text = None
        self.fetch_btn.disabled = True
        self.fetch_btn.text = "Analyzing..."
        self.page.update()

        def fetch_thread():
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    # Update UI with video info
                    video_title = info.get('title', 'Unknown Title')
                    if not video_title: video_title = 'Unknown Title'
                    
                    self.get_control("video_title").value = video_title
                    
                    duration = info.get('duration', 0)
                    if not duration: duration = 0
                    self.get_control("video_duration").value = f"{duration // 60}:{duration % 60:02d}"
                    
                    formats = []
                    if self.download_mode.value == "audio":
                        formats = [
                            {'id': 'bestaudio', 'label': 'Best Quality (192 kbps)', 'height': 999},
                            {'id': 'bestaudio[abr<=128]', 'label': 'Medium Quality (128 kbps)', 'height': 128}
                        ]
                    else:
                        seen_resolutions = set()
                        for f in info.get('formats', []):
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                height = f.get('height')
                                if height and height not in seen_resolutions:
                                    seen_resolutions.add(height)
                                    formats.append({'id': f.get('format_id'), 'label': f"{height}p", 'height': height})
                        formats.sort(key=lambda x: x['height'], reverse=True)

                    self.formats_data = formats
                    dropdown = self.get_control("format_dropdown")
                    dropdown.options = [ft.dropdown.Option(key=f['id'], text=f['label']) for f in formats]
                    if formats: dropdown.value = formats[0]['id']
                    
                    self.video_info_card.visible = True
                    self.video_info_card.opacity = 1
                    
            except Exception as ex:
                self.url_field.error_text = f"Error: {str(ex)}"
            finally:
                self.fetch_btn.disabled = False
                self.fetch_btn.text = "Analyze Video"
                self.page.update()

        threading.Thread(target=fetch_thread, daemon=True).start()

    def download_video(self, e):
        url = self.url_field.value.strip()
        format_id = self.get_control("format_dropdown").value
        
        if not url or not format_id: return

        btn = self.get_control("download_btn")
        btn.disabled = True
        btn.text = "Downloading..."
        
        self.progress_control.start_download()
        self.page.update()

        def download_thread():
            try:
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                    'progress_hooks': [self.progress_hook],
                }
                
                if self.download_mode.value == "audio":
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
                else:
                    ydl_opts['merge_output_format'] = 'mp4'

                if self.get_control("subtitle_checkbox").value:
                    ydl_opts.update({
                        'writesubtitles': True,
                        'subtitleslangs': [self.get_control("subtitle_lang_dropdown").value],
                        'subtitlesformat': 'srt'
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    filename = ydl.prepare_filename(info)
                    if self.download_mode.value == "audio":
                        filename = filename.rsplit('.', 1)[0] + '.mp3'
                    
                    ydl.download([url])
                    self.downloaded_file_path = filename

                self.progress_control.complete(
                    "✅ Download Complete!",
                    on_show_click=self.show_file
                )
                
            except Exception as ex:
                self.progress_control.error(str(ex))
            finally:
                btn.disabled = False
                btn.text = "Download Now"
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
            except Exception as e:
                print(f"Progress Error: {e}")

    def show_file(self, e):
        if hasattr(self, 'downloaded_file_path') and os.path.exists(self.downloaded_file_path):
            subprocess.run(['open', '-R', self.downloaded_file_path])

def main(page: ft.Page):
    YouTubeDownloaderAdvanced(page)

if __name__ == "__main__":
    ft.app(target=main)
