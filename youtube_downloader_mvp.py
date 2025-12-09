import flet as ft
import yt_dlp
import os
import subprocess
from pathlib import Path


class YouTubeDownloaderMVP:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Downloader - MVP"
        self.page.window_width = 650
        self.page.window_height = 550

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # FilePicker for folder selection
        self.file_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.file_picker)

        self.url_field = ft.TextField(
            label="YouTube URL",
            hint_text="https://www.youtube.com/watch?v=...",
            width=500,
        )

        # Download mode: Video or Audio
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="video", label="Video (MP4)"),
                ft.Radio(value="audio", label="Audio (MP3)")
            ]),
            value="video"
        )

        # Location selection
        self.location_field = ft.TextField(
            value=self.download_path,
            read_only=True,
            width=400,
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

        self.status_text = ft.Text("", color="blue")
        self.progress_bar = ft.ProgressBar(visible=False, width=500)
        self.progress_text = ft.Text("", visible=False)

        self.show_file_btn = ft.ElevatedButton(
            text="Show File",
            on_click=self.show_file,
            width=200,
            visible=False,
        )

        self.downloaded_file_path = None

        self.download_btn = ft.ElevatedButton(
            text="Start Download",
            on_click=self.download_video,
            width=200,
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("YouTube Downloader", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        self.url_field,
                        ft.Row([
                            ft.Text("Format:", size=14),
                            self.download_mode,
                        ], spacing=10),
                        self.location_row,
                        self.download_btn,
                        self.progress_bar,
                        self.progress_text,
                        self.status_text,
                        self.show_file_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=30,
            )
        )

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_path = e.path
            self.location_field.value = e.path
            self.page.update()

    def download_video(self, e):
        url = self.url_field.value.strip()

        if not url:
            self.status_text.value = "Iltimos, YouTube URL kiriting"
            self.status_text.color = "red"
            self.page.update()
            return

        self.download_btn.disabled = True
        self.show_file_btn.visible = False
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = "0%"
        self.status_text.value = "Yuklab olinmoqda..."
        self.status_text.color = "blue"
        self.page.update()

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
                }
                self.status_text.value = "Audio yuklanmoqda..."
            else:
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                    'progress_hooks': [self.progress_hook],
                    'merge_output_format': 'mp4',
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                }
                self.status_text.value = "Video yuklanmoqda..."

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
            self.progress_bar.visible = False
            self.page.update()

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
    YouTubeDownloaderMVP(page)


if __name__ == "__main__":
    ft.app(target=main)
