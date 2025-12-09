import flet as ft
import yt_dlp
import os
import subprocess
from pathlib import Path
import threading
import concurrent.futures
from threading import Lock


class VideoItem:
    def __init__(self, title, url, duration, thumbnail):
        self.title = title
        self.url = url
        self.duration = duration
        self.thumbnail = thumbnail
        self.selected = True
        self.status = "pending"
        self.progress = 0
        self.file_path = None
        self.download_mode = "video"  # video or audio


class PlaylistDownloader:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Playlist Downloader"
        self.page.window_width = 850
        self.page.window_height = 750

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # FilePicker for folder selection
        self.file_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.file_picker)

        self.videos = []
        self.video_controls = []
        self.downloading = False

        # Parallel download settings
        self.max_parallel = 2
        self.ui_lock = Lock()

        self.url_field = ft.TextField(
            label="Playlist URL",
            hint_text="https://www.youtube.com/playlist?list=...",
            width=600,
        )

        # Download mode: Video or Audio
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="video", label="Video (MP4)"),
                ft.Radio(value="audio", label="Audio (MP3)")
            ]),
            value="video"
        )

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

        self.fetch_btn = ft.ElevatedButton(
            text="Playlistni yuklash",
            on_click=self.fetch_playlist,
            width=200,
        )

        self.status_text = ft.Text("", size=14, color="blue")

        self.video_list_container = ft.Container(
            content=ft.Column(
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            height=350,
            border=ft.border.all(1, "#ddd"),
            border_radius=10,
            padding=ft.padding.only(left=10, right=10, top=10, bottom=20),
        )

        self.video_list = self.video_list_container.content

        self.select_all_checkbox = ft.Checkbox(
            label="Barchasini tanlash",
            value=True,
            on_change=self.toggle_select_all,
            visible=False,
        )

        self.download_info = ft.Text("", size=14, color="grey")

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

        self.parallel_slider = ft.Slider(
            min=1,
            max=3,
            divisions=2,
            label="Parallel: {value}",
            value=2,
            width=300,
            visible=False,
            on_change=self.on_parallel_change,
        )

        self.parallel_text = ft.Text(
            "Parallel yuklash: 2 ta",
            size=14,
            color="grey",
            visible=False,
        )

        self.download_btn = ft.ElevatedButton(
            text="Yuklashni boshlash",
            on_click=self.download_selected,
            width=300,
            height=50,
            visible=False,
            style=ft.ButtonStyle(
                color="white",
                bgcolor="#1976D2",
            ),
        )

        self.page.add(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Text("Playlist Downloader", size=28, weight=ft.FontWeight.BOLD),
                        padding=ft.padding.only(bottom=10, top=20),
                        alignment=ft.alignment.center,
                    ),
                    ft.Row(
                        [self.url_field, self.fetch_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Row([
                        ft.Text("Format:", size=14),
                        self.download_mode,
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    self.location_row,
                    self.status_text,
                    ft.Divider(height=20),
                    self.select_all_checkbox,
                    self.video_list_container,
                    self.download_info,
                    ft.Row([
                        self.subtitle_checkbox,
                        self.subtitle_lang_dropdown,
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Column([
                        self.parallel_text,
                        self.parallel_slider,
                    ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(
                        content=self.download_btn,
                        padding=ft.padding.only(top=10, bottom=20),
                        alignment=ft.alignment.center,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
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

    def on_parallel_change(self, e):
        # Update max_parallel when slider changes
        self.max_parallel = int(e.control.value)
        self.parallel_text.value = f"Parallel yuklash: {self.max_parallel} ta"
        self.page.update()

    def toggle_select_all(self, e):
        """Toggle all video selections"""
        select_all = e.control.value
        for video in self.videos:
            video.selected = select_all

        for control in self.video_controls:
            control['checkbox'].value = select_all

        # Update download info
        selected_count = len(self.videos) if select_all else 0
        self.download_info.value = f"📥 {selected_count} ta video tanlangan"
        self.page.update()

    def on_video_select(self, e, video):
        """Handle individual video selection"""
        video.selected = e.control.value

        # Update download info
        selected_count = sum(1 for v in self.videos if v.selected)
        self.download_info.value = f"📥 {selected_count} ta video tanlangan"
        self.page.update()

    def show_video_file(self, video):
        """Show video file in Finder/Explorer"""
        if video.file_path and os.path.exists(video.file_path):
            subprocess.run(['open', '-R', video.file_path])

    def fetch_playlist(self, _e):
        """Fetch videos from playlist"""
        url = self.url_field.value.strip()

        if not url:
            self.status_text.value = "Iltimos, Playlist URL kiriting"
            self.status_text.color = "red"
            self.page.update()
            return

        self.fetch_btn.disabled = True
        self.status_text.value = "Playlist yuklanmoqda..."
        self.status_text.color = "blue"
        self.page.update()

        def fetch_thread():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': 'in_playlist',
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    # Check if it's a playlist or single video
                    if 'entries' in info:
                        # It's a playlist
                        for entry in info['entries']:
                            if entry:
                                video = VideoItem(
                                    title=entry.get('title', 'Unknown'),
                                    url=entry.get('url', entry.get('id', '')),
                                    duration=entry.get('duration', 0),
                                    thumbnail=entry.get('thumbnail', None)
                                )
                                self.videos.append(video)
                    else:
                        # Single video
                        video = VideoItem(
                            title=info.get('title', 'Unknown'),
                            url=info.get('webpage_url', url),
                            duration=info.get('duration', 0),
                            thumbnail=info.get('thumbnail', None)
                        )
                        self.videos.append(video)

                    # Create UI for each video
                    self.video_list.controls.clear()
                    self.video_controls.clear()

                    for idx, video in enumerate(self.videos):
                        duration_min = video.duration // 60
                        duration_sec = video.duration % 60
                        duration_text = f"{duration_min}:{duration_sec:02d}"

                        checkbox = ft.Checkbox(
                            value=True,
                            on_change=lambda e, v=video: self.on_video_select(e, v)
                        )

                        status_icon = ft.Icon(
                            name=ft.Icons.PENDING,
                            color="grey",
                            size=20,
                        )

                        progress_bar = ft.ProgressBar(
                            value=0,
                            width=150,
                            visible=False,
                        )

                        progress_text = ft.Text(
                            "0%",
                            size=12,
                            visible=False,
                        )

                        show_file_btn = ft.IconButton(
                            icon=ft.Icons.FOLDER,
                            icon_size=20,
                            tooltip="Show file",
                            on_click=lambda e, v=video: self.show_video_file(v),
                            visible=False,
                        )

                        video_row = ft.Container(
                            content=ft.Row([
                                checkbox,
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text(
                                            video.title,
                                            size=14,
                                            weight=ft.FontWeight.W_500,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Row([
                                            ft.Icon(ft.Icons.TIMER, size=14, color="grey"),
                                            ft.Text(duration_text, size=12, color="grey"),
                                        ], spacing=4),
                                    ], spacing=4),
                                    expand=True,
                                ),
                                status_icon,
                                show_file_btn,
                                ft.Container(
                                    content=ft.Column([
                                        progress_bar,
                                        progress_text,
                                    ], spacing=4),
                                    width=150,
                                ),
                            ], spacing=10),
                            bgcolor="#ffffff",
                            border=ft.border.all(1, "#e0e0e0"),
                            border_radius=8,
                            padding=12,
                        )

                        self.video_controls.append({
                            'video': video,
                            'checkbox': checkbox,
                            'container': video_row,
                            'status_icon': status_icon,
                            'progress_bar': progress_bar,
                            'progress_text': progress_text,
                            'show_file_btn': show_file_btn,
                        })

                        self.video_list.controls.append(video_row)

                    self.status_text.value = f"✅ {len(self.videos)} ta video topildi"
                    self.status_text.color = "green"
                    self.select_all_checkbox.visible = True
                    self.download_info.value = f"📥 {len(self.videos)} ta video tanlangan"
                    self.subtitle_checkbox.visible = True
                    self.parallel_text.visible = True
                    self.parallel_slider.visible = True
                    self.download_btn.visible = True

            except Exception as ex:
                self.status_text.value = f"Xatolik: {str(ex)}"
                self.status_text.color = "red"

            self.fetch_btn.disabled = False
            self.page.update()

        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

    def download_selected(self, _e):
        """Download selected videos in parallel"""
        selected_videos = [v for v in self.videos if v.selected]

        if not selected_videos:
            self.status_text.value = "Iltimos, kamida bitta video tanlang"
            self.status_text.color = "red"
            self.page.update()
            return

        self.download_btn.disabled = True
        self.fetch_btn.disabled = True
        self.downloading = True
        self.status_text.value = f"Yuklab olinmoqda: 0/{len(selected_videos)}"
        self.status_text.color = "blue"
        self.page.update()

        def download_single_video(control):
            """Download a single video with UI lock for thread safety"""
            video = control['video']

            # Update status to downloading
            with self.ui_lock:
                control['container'].bgcolor = "#E3F2FD"
                control['status_icon'].name = ft.Icons.DOWNLOADING
                control['status_icon'].color = "#1976D2"
                control['progress_bar'].visible = True
                control['progress_bar'].value = 0
                control['progress_text'].visible = True
                control['progress_text'].value = "0%"
                self.page.update()

            try:
                # Check if url is already a full URL or just an ID
                if video.url.startswith('http'):
                    video_url = video.url
                else:
                    video_url = f"https://www.youtube.com/watch?v={video.url}"

                def progress_hook(d):
                    if d['status'] == 'downloading':
                        try:
                            if 'total_bytes' in d and d['total_bytes'] > 0:
                                percent = d['downloaded_bytes'] / d['total_bytes']
                                with self.ui_lock:
                                    control['progress_bar'].value = percent
                                    control['progress_text'].value = f"{int(percent * 100)}%"
                                    self.page.update()
                            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                                percent = d['downloaded_bytes'] / d['total_bytes_estimate']
                                with self.ui_lock:
                                    control['progress_bar'].value = percent
                                    control['progress_text'].value = f"{int(percent * 100)}%"
                                    self.page.update()
                        except Exception:
                            pass

                # Check if Audio or Video mode
                if self.download_mode.value == "audio":
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [progress_hook],
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
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                        'progress_hooks': [progress_hook],
                        'merge_output_format': 'mp4',
                        'postprocessors': [{
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': 'mp4',
                        }],
                        'quiet': True,
                        'no_warnings': True,
                    }

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

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    filename = ydl.prepare_filename(info)

                    # For audio, filename will have .mp3 extension
                    if self.download_mode.value == "audio":
                        filename = filename.rsplit('.', 1)[0] + '.mp3'

                    ydl.download([video_url])

                # Mark as completed
                with self.ui_lock:
                    control['container'].bgcolor = "#E8F5E9"
                    control['status_icon'].name = ft.Icons.CHECK_CIRCLE
                    control['status_icon'].color = "#4CAF50"
                    control['progress_bar'].visible = False
                    control['progress_text'].visible = False
                    control['show_file_btn'].visible = True
                    video.file_path = filename
                    video.status = "completed"
                    self.page.update()

                return True

            except Exception as ex:
                with self.ui_lock:
                    control['container'].bgcolor = "#FFEBEE"
                    control['status_icon'].name = ft.Icons.ERROR
                    control['status_icon'].color = "#F44336"
                    control['progress_bar'].visible = False
                    control['progress_text'].value = f"Xatolik: {str(ex)[:30]}"
                    video.status = "error"
                    self.page.update()
                return False

        def download_thread():
            # Get selected video controls
            selected_controls = [c for c in self.video_controls if c['video'].selected]
            completed = 0

            # Use ThreadPoolExecutor for parallel downloads
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                # Submit all download tasks
                future_to_control = {executor.submit(download_single_video, control): control for control in selected_controls}

                # Process completed downloads
                for future in concurrent.futures.as_completed(future_to_control):
                    if future.result():
                        completed += 1

                    with self.ui_lock:
                        self.status_text.value = f"Yuklab olinmoqda: {completed}/{len(selected_controls)}"
                        self.page.update()

            # All done
            with self.ui_lock:
                self.status_text.value = f"✅ {completed} ta video yuklandi!"
                self.status_text.color = "green"
                self.download_btn.disabled = False
                self.fetch_btn.disabled = False
                self.downloading = False
                self.page.update()

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()


def main(page: ft.Page):
    PlaylistDownloader(page)


if __name__ == "__main__":
    ft.app(target=main)
