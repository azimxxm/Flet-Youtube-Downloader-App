import flet as ft
import yt_dlp
import os
import subprocess
from pathlib import Path
import threading


class YouTubeDownloaderAdvanced:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Downloader - Advanced"
        self.page.window_width = 750
        self.page.window_height = 700

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # FilePicker for folder selection
        self.file_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.file_picker)

        self.formats_data = []

        self.url_field = ft.TextField(
            label="YouTube URL",
            hint_text="https://www.youtube.com/watch?v=...",
            width=600,
        )

        # Download mode: Video or Audio
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="video", label="Video (MP4)"),
                ft.Radio(value="audio", label="Audio (MP3)")
            ]),
            value="video",
            on_change=self.on_mode_change
        )

        # Location selection
        self.location_field = ft.TextField(
            value=self.download_path,
            read_only=True,
            width=450,
        )

        self.location_row = ft.Row([
            ft.Text("Saqlash joyi:", size=14),
            self.location_field,
            ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                tooltip="Joyni tanlash",
                on_click=lambda _: self.file_picker.get_directory_path()
            )
        ], spacing=10)

        self.fetch_btn = ft.ElevatedButton(
            text="Formatlarni ko'rish",
            on_click=self.fetch_formats,
            width=200,
        )

        self.format_dropdown = ft.Dropdown(
            label="Sifatni tanlang",
            width=600,
            visible=False,
        )

        self.subtitle_checkbox = ft.Checkbox(
            label="Subtitles yuklash",
            value=False,
            visible=False,
            on_change=self.on_subtitle_change,
        )

        self.subtitle_lang_dropdown = ft.Dropdown(
            label="Til tanlang",
            width=200,
            visible=False,
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("ru", "Русский"),
                ft.dropdown.Option("uz", "O'zbekcha"),
                ft.dropdown.Option("tr", "Türkçe"),
                ft.dropdown.Option("ar", "العربية"),
                ft.dropdown.Option("es", "Español"),
                ft.dropdown.Option("fr", "Français"),
                ft.dropdown.Option("de", "Deutsch"),
            ],
            value="en",
        )

        self.video_info = ft.Column(visible=False, spacing=10)

        self.download_btn = ft.ElevatedButton(
            text="Start Download",
            on_click=self.download_video,
            width=200,
            visible=False,
        )

        self.status_text = ft.Text("", color="blue")
        self.progress_bar = ft.ProgressBar(visible=False, width=600)
        self.progress_text = ft.Text("", visible=False)

        self.show_file_btn = ft.ElevatedButton(
            text="Show File",
            on_click=self.show_file,
            width=200,
            visible=False,
        )

        self.downloaded_file_path = None

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("YouTube Downloader - Advanced", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        self.url_field,
                        ft.Row([
                            ft.Text("Format:", size=14),
                            self.download_mode,
                        ], spacing=10),
                        self.location_row,
                        self.fetch_btn,
                        self.video_info,
                        self.format_dropdown,
                        ft.Row([
                            self.subtitle_checkbox,
                            self.subtitle_lang_dropdown,
                        ], spacing=10),
                        self.download_btn,
                        self.progress_bar,
                        self.progress_text,
                        self.status_text,
                        self.show_file_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=30,
            )
        )

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_path = e.path
            self.location_field.value = e.path
            self.page.update()

    def on_subtitle_change(self, _e):
        # Show/hide language dropdown based on checkbox
        self.subtitle_lang_dropdown.visible = self.subtitle_checkbox.value
        self.page.update()

    def on_mode_change(self, _e):
        # Reset format selection when mode changes
        self.format_dropdown.visible = False
        self.subtitle_checkbox.visible = False
        self.subtitle_lang_dropdown.visible = False
        self.download_btn.visible = False
        self.video_info.visible = False
        self.page.update()

    def fetch_formats(self, _e):
        url = self.url_field.value.strip()

        if not url:
            self.status_text.value = "Iltimos, YouTube URL kiriting"
            self.status_text.color = "red"
            self.page.update()
            return

        self.fetch_btn.disabled = True
        self.status_text.value = "Ma'lumotlar yuklanmoqda..."
        self.status_text.color = "blue"
        self.page.update()

        def fetch_thread():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    self.video_info.controls = [
                        ft.Text(f"Nomi: {info.get('title', 'N/A')}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Davomiyligi: {info.get('duration', 0) // 60} daqiqa"),
                    ]
                    self.video_info.visible = True

                    formats = []

                    # Audio mode - show audio quality options
                    if self.download_mode.value == "audio":
                        formats.append({
                            'id': 'bestaudio',
                            'label': 'Best Quality (192 kbps)',
                            'height': 999
                        })
                        formats.append({
                            'id': 'bestaudio[abr<=128]',
                            'label': 'Medium Quality (128 kbps)',
                            'height': 128
                        })
                    else:
                        # Video mode - show video resolutions
                        seen_resolutions = set()

                        for f in info.get('formats', []):
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                height = f.get('height')
                                ext = f.get('ext', 'mp4')
                                format_id = f.get('format_id')

                                if height and height not in seen_resolutions:
                                    seen_resolutions.add(height)
                                    formats.append({
                                        'id': format_id,
                                        'label': f"{height}p",
                                        'height': height
                                    })

                    formats.sort(key=lambda x: x['height'], reverse=True)

                    self.formats_data = formats
                    self.format_dropdown.options = [
                        ft.dropdown.Option(key=f['id'], text=f['label'])
                        for f in formats
                    ]

                    if formats:
                        self.format_dropdown.value = formats[0]['id']

                    self.format_dropdown.visible = True
                    self.subtitle_checkbox.visible = True
                    self.download_btn.visible = True
                    self.status_text.value = "Formatlar yuklandi. Sifatni tanlang."
                    self.status_text.color = "green"

            except Exception as ex:
                self.status_text.value = f"Xatolik: {str(ex)}"
                self.status_text.color = "red"

            finally:
                self.fetch_btn.disabled = False
                self.page.update()

        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

    def download_video(self, _e):
        url = self.url_field.value.strip()
        selected_format = self.format_dropdown.value

        if not url or not selected_format:
            self.status_text.value = "URL va formatni tanlang"
            self.status_text.color = "red"
            self.page.update()
            return

        self.download_btn.disabled = True
        self.fetch_btn.disabled = True
        self.show_file_btn.visible = False
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = "0%"
        self.status_text.value = "Yuklab olinmoqda..."
        self.status_text.color = "blue"
        self.page.update()

        def download_thread():
            try:
                # Check if Audio or Video mode
                if self.download_mode.value == "audio":
                    ydl_opts = {
                        'format': selected_format,
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [self.progress_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }
                    self.status_text.value = "Audio yuklanmoqda..."
                else:
                    ydl_opts = {
                        'format': selected_format,
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [self.progress_hook],
                        'merge_output_format': 'mp4',
                        'postprocessors': [{
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': 'mp4',
                        }],
                    }
                    self.status_text.value = "Video yuklanmoqda..."

                # Add subtitle options if checkbox is checked
                if self.subtitle_checkbox.value:
                    selected_lang = self.subtitle_lang_dropdown.value
                    ydl_opts.update({
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': [selected_lang],
                        'subtitlesformat': 'srt',
                        'ignoreerrors': True,
                    })

                self.status_text.color = "blue"
                self.page.update()

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    filename = ydl.prepare_filename(info)

                    # For audio, filename will have .mp3 extension
                    if self.download_mode.value == "audio":
                        filename = filename.rsplit('.', 1)[0] + '.mp3'

                    ydl.download([url])
                    self.downloaded_file_path = filename

                mode_text = "Audio" if self.download_mode.value == "audio" else "Video"
                self.status_text.value = f"{mode_text} muvaffaqiyatli yuklandi"
                self.status_text.color = "green"
                self.show_file_btn.visible = True

            except Exception as ex:
                self.status_text.value = f"Xatolik: {str(ex)}"
                self.status_text.color = "red"

            finally:
                self.download_btn.disabled = False
                self.fetch_btn.disabled = False
                self.progress_bar.visible = False
                self.page.update()

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    percent = d['downloaded_bytes'] / d['total_bytes']
                    self.progress_bar.value = percent
                    self.progress_text.value = f"{int(percent * 100)}%"
                    self.page.update()
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    percent = d['downloaded_bytes'] / d['total_bytes_estimate']
                    self.progress_bar.value = percent
                    self.progress_text.value = f"{int(percent * 100)}%"
                    self.page.update()
                elif 'downloaded_bytes' in d:
                    downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                    self.progress_text.value = f"{downloaded_mb:.1f}MB"
                    self.page.update()
            except Exception:
                pass

    def show_file(self, _e):
        if self.downloaded_file_path and os.path.exists(self.downloaded_file_path):
            subprocess.run(['open', '-R', self.downloaded_file_path])


def main(page: ft.Page):
    YouTubeDownloaderAdvanced(page)


if __name__ == "__main__":
    ft.app(target=main)
