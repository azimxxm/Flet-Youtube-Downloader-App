import flet as ft
import yt_dlp
import os
import subprocess
from pathlib import Path
import threading
import time
from ui_components import ProgressControl


class InstagramDownloader:
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.page.title = "Instagram Downloader"
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
        self.download_path = str(Path.home() / "Downloads" / "Instagram")
        Path(self.download_path).mkdir(parents=True, exist_ok=True)

        # FilePicker
        self.file_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.file_picker)

        self.media_info = None
        self.cancel_download = False
        self.init_ui()

    def init_ui(self):
        # Header
        header_content = [
            ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, size=32, color="#E4405F"),
            ft.Text("Instagram Downloader", size=20, weight=ft.FontWeight.BOLD, color="white"),
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
            padding=ft.padding.only(top=20, bottom=15, left=20, right=20),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#2d2d2d", "#1a1a1a"],
            ),
        )

        # Input Section
        self.url_field = ft.TextField(
            label="Instagram URL",
            hint_text="Paste link here...",
            border_radius=10,
            bgcolor="#2d2d2d",
            border_color="#404040",
            focused_border_color="#E4405F",
            text_style=ft.TextStyle(color="white", size=13),
            label_style=ft.TextStyle(color="#aaaaaa", size=12),
            prefix_icon=ft.Icons.LINK,
            height=50,
            expand=True
        )

        self.analyze_btn = ft.ElevatedButton(
            text="Analyze",
            icon=ft.Icons.SEARCH,
            style=ft.ButtonStyle(
                color="white",
                bgcolor={"": "#E4405F", "hovered": "#C13584"},
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            height=50,
            on_click=self.analyze_media,
        )

        # Media Preview Section (Hidden initially) - Compact
        self.preview_image = ft.Image(
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=10,
            visible=False
        )

        self.media_title = ft.Text(
            "",
            size=13,
            color="white",
            weight=ft.FontWeight.W_500,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            visible=False,
        )

        self.media_type = ft.Text(
            "",
            size=11,
            color="#888888",
            visible=False
        )

        # Download Options - Horizontal layout (Hidden initially)
        self.download_options = ft.RadioGroup(
            content=ft.Row([
                self.create_radio_option_compact("Video", "video", ft.Icons.VIDEOCAM),
                self.create_radio_option_compact("Audio", "audio", ft.Icons.AUDIOTRACK),
                self.create_radio_option_compact("Photo", "photo", ft.Icons.PHOTO),
                self.create_radio_option_compact("Thumb", "thumbnail", ft.Icons.IMAGE),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            value="video",
            visible=False
        )

        self.download_btn = ft.ElevatedButton(
            text="Download",
            icon=ft.Icons.DOWNLOAD,
            style=ft.ButtonStyle(
                color="white",
                bgcolor={"": ft.Colors.GREEN_ACCENT, "hovered": ft.Colors.GREEN_700},
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            height=45,
            visible=False,
            on_click=self.start_download,
        )

        # Folder Path Section - Compact
        self.folder_path_text = ft.Text(
            f"📁 {Path(self.download_path).name}",
            size=11,
            color="#888888",
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS
        )

        self.choose_folder_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            icon_color="#E4405F",
            tooltip="Change Folder",
            on_click=lambda _: self.file_picker.get_directory_path(),
        )

        # Progress Section
        self.progress_control = ProgressControl(width=650)

        # Preview Card (Hidden initially)
        self.preview_card = ft.Container(
            content=ft.Row([
                self.preview_image,
                ft.Container(width=10),
                ft.Column([
                    self.media_title,
                    self.media_type,
                ], spacing=5, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.START),
            visible=False,
            padding=15,
            bgcolor="#252525",
            border_radius=10,
        )

        # Options Container (Hidden initially)
        self.options_container = ft.Container(
            content=ft.Column([
                ft.Text("Download Type", size=14, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=8),
                self.download_options,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=False,
        )

        # Build UI - Single Screen Layout
        self.page.add(
            ft.Column(
                [
                    self.header,
                    ft.Container(
                        content=ft.Column([
                            # Input Row
                            ft.Row([
                                self.url_field,
                                self.analyze_btn,
                            ], spacing=10),
                            ft.Container(height=15),

                            # Preview Card
                            self.preview_card,
                            ft.Container(height=15),

                            # Options & Download Button
                            self.options_container,
                            ft.Container(height=10),
                            self.download_btn,
                            ft.Container(height=15),

                            # Progress
                            self.progress_control,
                            ft.Container(height=10),

                            # Footer - Folder path
                            ft.Row([
                                self.folder_path_text,
                                self.choose_folder_btn,
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        expand=True,
                    )
                ],
                spacing=0,
                expand=True,
            )
        )

    def create_radio_option(self, label, value, icon):
        return ft.Container(
            content=ft.Row([
                ft.Radio(value=value, fill_color="#E4405F"),
                ft.Icon(icon, size=20, color="#E4405F"),
                ft.Text(label, size=14, color="white"),
            ], spacing=10),
            bgcolor="#252525",
            padding=10,
            border_radius=8,
        )

    def create_radio_option_compact(self, label, value, icon):
        return ft.Container(
            content=ft.Column([
                ft.Radio(value=value, fill_color="#E4405F"),
                ft.Icon(icon, size=18, color="#E4405F"),
                ft.Text(label, size=11, color="white", text_align=ft.TextAlign.CENTER),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#252525",
            padding=8,
            border_radius=8,
            width=80,
        )

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.download_path = e.path
            self.folder_path_text.value = f"📁 {Path(self.download_path).name}"
            self.page.update()

    def analyze_media(self, e):
        url = self.url_field.value.strip()
        if not url:
            self.show_error("Please enter an Instagram URL")
            return

        # Reset UI
        self.preview_card.visible = False
        self.download_options.visible = False
        self.options_container.visible = False
        self.download_btn.visible = False
        self.progress_control.reset()

        # Show loading
        self.analyze_btn.disabled = True
        self.analyze_btn.text = "Analyzing..."
        self.page.update()

        def analyze_thread():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    self.media_info = info

                    # Update UI with media info
                    self.page.run_task(self.update_preview, info)

            except Exception as ex:
                self.page.run_task(self.show_error, f"Failed to analyze: {str(ex)}")
            finally:
                self.analyze_btn.disabled = False
                self.analyze_btn.text = "Analyze"
                self.page.update()

        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()

    async def update_preview(self, info):
        # Get thumbnail
        thumbnail = info.get('thumbnail', '')
        if thumbnail:
            self.preview_image.src = thumbnail
            self.preview_image.visible = True

        # Get title/description
        title = info.get('title', info.get('description', 'Instagram Media'))
        if len(title) > 80:
            title = title[:80] + "..."
        self.media_title.value = title
        self.media_title.visible = True

        # Determine media type and get size info
        formats = info.get('formats', [])
        has_video = any(f.get('vcodec') != 'none' for f in formats)
        has_audio = any(f.get('acodec') != 'none' for f in formats)

        # Get file size
        filesize = 0
        for f in formats:
            if f.get('filesize'):
                filesize = max(filesize, f.get('filesize', 0))
            elif f.get('filesize_approx'):
                filesize = max(filesize, f.get('filesize_approx', 0))

        size_text = ""
        if filesize > 0:
            if filesize > 1024 * 1024:
                size_text = f" • {filesize / 1024 / 1024:.1f}MB"
            else:
                size_text = f" • {filesize / 1024:.1f}KB"

        if has_video:
            media_type_text = f"📹 Video{size_text}"
        elif has_audio:
            media_type_text = f"🎵 Audio{size_text}"
        else:
            media_type_text = f"📷 Photo{size_text}"

        self.media_type.value = media_type_text
        self.media_type.visible = True

        # Show preview card
        self.preview_card.visible = True

        # Show download options
        self.download_options.visible = True
        self.options_container.visible = True

        # Auto-select appropriate option
        if has_video:
            self.download_options.value = "video"
        elif has_audio:
            self.download_options.value = "audio"
        else:
            self.download_options.value = "photo"

        self.download_btn.visible = True
        self.page.update()

    async def show_error(self, message):
        self.progress_control.error(message)

    def start_download(self, e):
        if not self.media_info:
            self.show_error("Please analyze a link first")
            return

        self.cancel_download = False
        download_type = self.download_options.value

        self.download_btn.disabled = True
        self.analyze_btn.disabled = True

        def on_cancel(_e):
            self.cancel_download = True

        self.progress_control.start_download(
            message=f"Downloading {download_type}...",
            on_cancel=on_cancel
        )

        def download_thread():
            downloaded_file_path = None

            try:
                # Prepare filename
                safe_title = "".join(c for c in self.media_info.get('title', 'instagram_media')[:50]
                                   if c.isalnum() or c in (' ', '-', '_')).strip()

                if not safe_title:
                    safe_title = "instagram_media"

                output_template = os.path.join(self.download_path, f"{safe_title}.%(ext)s")

                if download_type == "thumbnail":
                    # Download thumbnail directly
                    import urllib.request
                    thumbnail_url = self.media_info.get('thumbnail', '')
                    if thumbnail_url:
                        # Determine extension from URL
                        ext = 'jpg'
                        if '.png' in thumbnail_url:
                            ext = 'png'
                        elif '.webp' in thumbnail_url:
                            ext = 'webp'

                        thumbnail_path = os.path.join(self.download_path, f"{safe_title}_thumbnail.{ext}")

                        # Show progress
                        async def update_thumb_progress():
                            self.progress_control.update_progress(0.5, "Downloading thumbnail...")
                        self.page.run_task(update_thumb_progress)

                        urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
                        downloaded_file_path = thumbnail_path
                    else:
                        raise Exception("No thumbnail available")

                elif download_type == "video":
                    ydl_opts = {
                        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                        'outtmpl': output_template,
                        'progress_hooks': [self.progress_hook],
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(self.media_info['webpage_url'], download=True)
                        # Get the actual filename from yt-dlp
                        if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                            downloaded_file_path = info['requested_downloads'][0].get('filepath')
                        elif '_filename' in info:
                            downloaded_file_path = info['_filename']

                elif download_type == "audio":
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': output_template,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'progress_hooks': [self.progress_hook],
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(self.media_info['webpage_url'], download=True)
                        # Get the actual filename from yt-dlp
                        if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                            downloaded_file_path = info['requested_downloads'][0].get('filepath')
                        elif '_filename' in info:
                            downloaded_file_path = info['_filename']

                elif download_type == "photo":
                    # For photos, we need to avoid downloading video
                    ydl_opts = {
                        'format': 'best[vcodec=none]/best',  # Try to get non-video format
                        'outtmpl': output_template,
                        'progress_hooks': [self.progress_hook],
                        'writethumbnail': False,
                    }

                    # Check if media actually has photos
                    formats = self.media_info.get('formats', [])
                    has_photo = any(f.get('vcodec') == 'none' and f.get('acodec') == 'none' for f in formats)

                    if not has_photo:
                        # This is a video/audio post, not a photo - download thumbnail instead
                        import urllib.request
                        thumbnail_url = self.media_info.get('thumbnail', '')
                        if thumbnail_url:
                            ext = 'jpg'
                            if '.png' in thumbnail_url:
                                ext = 'png'
                            elif '.webp' in thumbnail_url:
                                ext = 'webp'

                            thumbnail_path = os.path.join(self.download_path, f"{safe_title}_photo.{ext}")

                            # Show progress
                            async def update_photo_progress():
                                self.progress_control.update_progress(0.5, "Downloading image...")
                            self.page.run_task(update_photo_progress)

                            urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
                            downloaded_file_path = thumbnail_path
                        else:
                            raise Exception("This post doesn't contain photos. Try Video or Thumbnail option.")
                    else:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(self.media_info['webpage_url'], download=True)
                            # Get the actual filename from yt-dlp
                            if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                                downloaded_file_path = info['requested_downloads'][0].get('filepath')
                            elif '_filename' in info:
                                downloaded_file_path = info['_filename']

                if not self.cancel_download:
                    # Find the downloaded file
                    expected_file = downloaded_file_path

                    # If we couldn't get the path from yt-dlp, search for it
                    if not expected_file or not os.path.exists(expected_file):
                        if download_type == "audio":
                            expected_file = os.path.join(self.download_path, f"{safe_title}.mp3")
                        else:
                            # Try common extensions
                            for ext in ['mp4', 'jpg', 'jpeg', 'png', 'webp']:
                                test_file = os.path.join(self.download_path, f"{safe_title}.{ext}")
                                if os.path.exists(test_file):
                                    expected_file = test_file
                                    break

                    # If still not found, get the most recent file in download folder
                    if not expected_file or not os.path.exists(expected_file):
                        download_folder = Path(self.download_path)
                        files = list(download_folder.glob('*'))
                        if files:
                            expected_file = str(max(files, key=lambda f: f.stat().st_mtime))

                    # Store file path for closure
                    final_file_path = expected_file

                    async def show_complete():
                        def on_show_click(_e):
                            if final_file_path and os.path.exists(final_file_path):
                                subprocess.run(["open", "-R", final_file_path])

                        self.progress_control.complete(
                            message="✅ Download Complete!",
                            on_show_click=on_show_click
                        )
                        self.download_btn.disabled = False
                        self.analyze_btn.disabled = False

                    self.page.run_task(show_complete)
                else:
                    async def show_cancelled():
                        self.progress_control.cancelled()
                        self.download_btn.disabled = False
                        self.analyze_btn.disabled = False

                    self.page.run_task(show_cancelled)

            except Exception as ex:
                error_msg = str(ex)

                async def show_error_msg():
                    if not self.cancel_download:
                        self.progress_control.error(f"Download failed: {error_msg}")
                    self.download_btn.disabled = False
                    self.analyze_btn.disabled = False

                self.page.run_task(show_error_msg)

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def progress_hook(self, d):
        if self.cancel_download:
            raise Exception("Download cancelled by user")

        if d['status'] == 'downloading':
            try:
                percent = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) if d.get('total_bytes') else 0
                speed = d.get('speed_str', 'N/A')
                eta = d.get('eta_str', 'N/A')

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0)
                if total > 0:
                    size_info = f"{downloaded / 1024 / 1024:.1f}MB / {total / 1024 / 1024:.1f}MB"
                else:
                    size_info = f"{downloaded / 1024 / 1024:.1f}MB"

                self.progress_control.update_progress(
                    percent=percent,
                    speed=speed,
                    eta=eta,
                    size_info=size_info
                )
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_control.update_progress(1.0, "Processing...")
