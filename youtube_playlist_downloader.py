import flet as ft
import yt_dlp
import os
import subprocess
import sys
from pathlib import Path
import threading
import concurrent.futures
from threading import Lock
from ui_components import RadioOptionComponent
from utils import validate_youtube_url, check_ffmpeg_installed, get_responsive_dimensions

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
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.page.title = "YouTube Playlist Downloader"

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

        self.videos = []
        self.video_controls = []
        self.downloading = False

        # Parallel download settings
        self.max_parallel = 2
        self.ui_lock = Lock()

        # Keyboard shortcuts
        self.page.on_keyboard_event = self.on_keyboard

        self.init_ui()

    def init_ui(self):
        # Header
        header_content = [
            ft.Icon(ft.Icons.PLAYLIST_PLAY_ROUNDED, size=40, color=ft.Colors.BLUE_ACCENT),
            ft.Text("Playlist Downloader", size=24, weight=ft.FontWeight.BOLD, color="white"),
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

        # Input Section
        self.url_field = ft.TextField(
            label="Playlist URL",
            hint_text="Paste playlist link here...",
            width=500,
            border_radius=10,
            bgcolor="#2d2d2d",
            border_color="#404040",
            focused_border_color=ft.Colors.BLUE_ACCENT,
            text_style=ft.TextStyle(color="white"),
            label_style=ft.TextStyle(color="#aaaaaa"),
            prefix_icon=ft.Icons.LINK,
        )

        self.fetch_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.SEARCH, color="white"),
                ft.Text("Load Playlist", color="white"),
            ], spacing=10),
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.BLUE_ACCENT, "hovered": ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
            width=180,
            on_click=self.fetch_playlist,
        )

        # Mode Selection
        self.download_mode = ft.RadioGroup(
            content=ft.Row([
                RadioOptionComponent("Video (MP4)", "video", ft.Icons.VIDEOCAM, ft.Colors.BLUE_ACCENT),
                RadioOptionComponent("Audio (MP3)", "audio", ft.Icons.AUDIOTRACK, ft.Colors.BLUE_ACCENT),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            value="video"
        )

        # Location Section
        self.location_text = ft.Text(self.download_path, size=12, color="#888888", italic=True)
        self.location_container = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=16, color="#888888"),
                self.location_text,
                ft.TextButton("Change", on_click=self.open_file_picker, style=ft.ButtonStyle(color=ft.Colors.BLUE_ACCENT))
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
        )

        # Video List Container
        self.video_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.video_list_container = ft.Container(
            content=self.video_list,
            height=400,
            bgcolor="#252525",
            border_radius=10,
            border=ft.Border.all(1, "#333333"),
            padding=10,
            expand=True,
            visible=False,
        )

        # Controls
        self.select_all_checkbox = ft.Checkbox(
            label="Select All",
            value=True,
            on_change=self.toggle_select_all,
            visible=False,
            fill_color=ft.Colors.BLUE_ACCENT,
        )

        self.download_info = ft.Text("", size=14, color="#aaaaaa")

        self.status_text = ft.Text("", size=14, color="#aaaaaa")

        # Loading Progress View
        self.loading_spinner = ft.Text("◐", size=40, color=ft.Colors.BLUE_ACCENT)
        self.loading_progress = ft.Container(
            content=ft.Column([
                self.loading_spinner,
                ft.Text(
                    "Analyzing playlist...",
                    size=16,
                    color="white",
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Please wait...",
                    size=12,
                    color="#888888",
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            padding=30,
            bgcolor="#252525",
            border_radius=15,
            border=ft.Border.all(1, "#333333"),
            visible=False,
        )

        self.download_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, color="white"),
                ft.Text("Start Download", color="white"),
            ], spacing=10),
            on_click=self.download_selected,
            width=300,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.GREEN_600, "hovered": ft.Colors.GREEN_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
        )

        # Main Layout
        self.page.add(
            ft.Column(
                [
                    self.header,
                    ft.Container(
                        content=ft.Column([
                            ft.Row([self.url_field, self.fetch_btn], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=10),
                            self.download_mode,
                            self.location_container,
                            self.status_text,
                            self.loading_progress,
                            ft.Container(height=10),
                            ft.Row([self.select_all_checkbox, self.download_info], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            self.video_list_container,
                            ft.Container(height=10),
                            self.download_btn,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=30,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
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
        self.page.run_task(self.file_picker.get_directory_path)

    def toggle_select_all(self, e):
        select_all = e.control.value
        for video in self.videos:
            video.selected = select_all
        for control in self.video_controls:
            control['checkbox'].value = select_all
        
        selected_count = len(self.videos) if select_all else 0
        self.download_info.value = f"📥 {selected_count} videos selected"
        self.page.update()

    def on_video_select(self, e, video):
        video.selected = e.control.value
        selected_count = sum(1 for v in self.videos if v.selected)
        self.download_info.value = f"📥 {selected_count} videos selected"
        self.page.update()

    def show_video_file(self, video):
        if video.file_path and os.path.exists(video.file_path):
            subprocess.run(['open', '-R', video.file_path])

    def fetch_playlist(self, _e):
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

        self.url_field.error_text = None
        self.fetch_btn.disabled = True
        self.status_text.value = ""
        self.loading_progress.visible = True
        self.page.update()

        def fetch_thread():
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': 'in_playlist'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    self.videos = []
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry:
                                self.videos.append(VideoItem(
                                    title=entry.get('title', 'Unknown'),
                                    url=entry.get('url', entry.get('id', '')),
                                    duration=entry.get('duration', 0),
                                    thumbnail=entry.get('thumbnail', None)
                                ))
                    else:
                        self.videos.append(VideoItem(
                            title=info.get('title', 'Unknown'),
                            url=info.get('webpage_url', url),
                            duration=info.get('duration', 0),
                            thumbnail=info.get('thumbnail', None)
                        ))

                    self.video_list.controls.clear()
                    self.video_controls.clear()

                    for video in self.videos:
                        duration = f"{video.duration // 60}:{video.duration % 60:02d}"

                        checkbox = ft.Checkbox(value=True, on_change=lambda e, v=video: self.on_video_select(e, v), fill_color=ft.Colors.BLUE_ACCENT)
                        status_icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color="#666666", size=20)
                        progress_bar = ft.ProgressBar(value=0, width=100, visible=False, color=ft.Colors.BLUE_ACCENT, bgcolor="#444444")
                        show_btn = ft.IconButton(ft.Icons.FOLDER, icon_color="white", visible=False, on_click=lambda e, v=video: self.show_video_file(v))

                        row = ft.Container(
                            content=ft.Row([
                                checkbox,
                                ft.Column([
                                    ft.Text(video.title, size=14, weight=ft.FontWeight.W_500, color="white", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, width=400),
                                    ft.Text(duration, size=12, color="#888888")
                                ], spacing=2),
                                ft.Container(expand=True),
                                status_icon,
                                progress_bar,
                                show_btn
                            ], alignment=ft.MainAxisAlignment.START),
                            bgcolor="#333333",
                            padding=10,
                            border_radius=8
                        )

                        self.video_controls.append({
                            'video': video, 'checkbox': checkbox, 'container': row,
                            'status_icon': status_icon, 'progress_bar': progress_bar, 'show_file_btn': show_btn
                        })
                        self.video_list.controls.append(row)

                    async def update_ui_success():
                        self.loading_progress.visible = False
                        self.status_text.value = f"✅ Found {len(self.videos)} videos"
                        self.status_text.color = ft.Colors.GREEN_ACCENT
                        self.select_all_checkbox.visible = True
                        self.video_list_container.visible = True
                        self.download_info.value = f"📥 {len(self.videos)} videos selected"
                        self.download_btn.visible = True
                        self.fetch_btn.disabled = False
                        self.page.update()

                    self.page.run_task(update_ui_success)

            except Exception as ex:
                from utils import translate_error
                user_msg = translate_error(ex)

                async def update_ui_error():
                    self.loading_progress.visible = False
                    self.status_text.value = f"❌ Error: {user_msg}"
                    self.status_text.color = ft.Colors.RED_ACCENT
                    self.fetch_btn.disabled = False
                    self.page.update()

                self.page.run_task(update_ui_error)

        threading.Thread(target=fetch_thread, daemon=True).start()

    def download_selected(self, _e):
        selected_videos = [v for v in self.videos if v.selected]
        if not selected_videos: return

        # Check FFmpeg installation
        ffmpeg_ok, ffmpeg_error = check_ffmpeg_installed()
        if not ffmpeg_ok:
            self.status_text.value = f"❌ Error: {ffmpeg_error}"
            self.status_text.color = ft.Colors.RED_ACCENT
            self.page.update()
            return

        self.download_btn.disabled = True
        self.fetch_btn.disabled = True
        self.downloading = True
        self.status_text.value = f"Downloading: 0/{len(selected_videos)}"
        self.page.update()

        def download_single_video(control):
            video = control['video']
            with self.ui_lock:
                control['status_icon'].name = ft.Icons.DOWNLOADING
                control['status_icon'].color = ft.Colors.BLUE_ACCENT
                control['progress_bar'].visible = True
                self.page.update()

            try:
                video_url = video.url if video.url.startswith('http') else f"https://www.youtube.com/watch?v={video.url}"
                
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        try:
                            if 'total_bytes' in d and d['total_bytes'] > 0:
                                percent = d['downloaded_bytes'] / d['total_bytes']
                                with self.ui_lock: control['progress_bar'].value = percent; self.page.update()
                        except Exception:
                            pass

                ydl_opts = {
                    'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                    'progress_hooks': [progress_hook],
                    'quiet': True, 'no_warnings': True
                }
                
                if self.download_mode.value == "audio":
                    ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})
                else:
                    ydl_opts.update({'format': 'bestvideo[vcodec=h264][ext=mp4]+bestaudio[acodec=aac][ext=m4a]/best[ext=mp4]/best', 'merge_output_format': 'mp4'})

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    filename = ydl.prepare_filename(info)
                    if self.download_mode.value == "audio": filename = filename.rsplit('.', 1)[0] + '.mp3'
                    ydl.download([video_url])
                    video.file_path = filename

                with self.ui_lock:
                    control['status_icon'].name = ft.Icons.CHECK_CIRCLE
                    control['status_icon'].color = ft.Colors.GREEN_ACCENT
                    control['progress_bar'].visible = False
                    control['show_file_btn'].visible = True
                    self.page.update()
                return True

            except Exception as ex:
                with self.ui_lock:
                    control['status_icon'].name = ft.Icons.ERROR
                    control['status_icon'].color = ft.Colors.RED_ACCENT
                    control['progress_bar'].visible = False
                    self.page.update()
                return False

        def download_thread():
            selected_controls = [c for c in self.video_controls if c['video'].selected]
            completed = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                future_to_control = {executor.submit(download_single_video, control): control for control in selected_controls}
                for future in concurrent.futures.as_completed(future_to_control):
                    if future.result(): completed += 1
                    with self.ui_lock:
                        self.status_text.value = f"Downloading: {completed}/{len(selected_controls)}"
                        self.page.update()

            with self.ui_lock:
                self.status_text.value = f"✅ {completed} videos downloaded!"
                self.download_btn.disabled = False
                self.fetch_btn.disabled = False
                self.downloading = False
                self.page.update()

        threading.Thread(target=download_thread, daemon=True).start()

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
            self.download_selected(None)
        elif ctrl and e.key.lower() == "t":
            # Toggle theme
            from ui_components import ThemeManager
            ThemeManager.toggle_theme(self.page)


def main(page: ft.Page):
    PlaylistDownloader(page)

if __name__ == "__main__":
    ft.run(main)
