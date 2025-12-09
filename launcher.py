import flet as ft
import subprocess
import sys
import os
import platform
import threading
import time


class SetupWindow:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Downloader - Setup"
        self.page.window_width = 600
        self.page.window_height = 500

        self.checks = {
            'python': {'name': 'Python 3.7+', 'status': 'pending', 'icon': None},
            'flet': {'name': 'Flet kutubxonasi', 'status': 'pending', 'icon': None},
            'yt_dlp': {'name': 'yt-dlp kutubxonasi', 'status': 'pending', 'icon': None},
            'ffmpeg': {'name': 'FFmpeg', 'status': 'pending', 'icon': None},
        }

        self.check_items = {}
        self.install_btn = None
        self.get_started_btn = None
        self.status_text = None
        self.setup_complete = False

        self.build_ui()
        self.start_initial_check()

    def build_ui(self):
        """Build the UI"""
        check_list = ft.Column(spacing=15)

        for key, info in self.checks.items():
            icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color="grey", size=24)
            self.checks[key]['icon'] = icon

            row = ft.Row(
                [
                    icon,
                    ft.Text(info['name'], size=16),
                ],
                spacing=10,
            )
            self.check_items[key] = row
            check_list.controls.append(row)

        self.status_text = ft.Text("", size=14, color="blue", text_align=ft.TextAlign.CENTER)

        self.install_btn = ft.ElevatedButton(
            text="Install qilish",
            on_click=self.install_dependencies,
            width=200,
            visible=False,
            disabled=True,
        )

        self.get_started_btn = ft.ElevatedButton(
            text="Boshlash",
            on_click=self.start_app,
            width=200,
            visible=False,
            style=ft.ButtonStyle(
                color="white",
                bgcolor="green",
            ),
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("YouTube Downloader", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Tizim tekshiruvi", size=16, color="grey"),
                        ft.Divider(),
                        check_list,
                        ft.Divider(),
                        self.status_text,
                        ft.Row(
                            [self.install_btn, self.get_started_btn],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        )

    def update_check_status(self, key, status):
        """Update check status: pending, checking, success, failed"""
        if status == 'checking':
            self.checks[key]['icon'].name = ft.Icons.SYNC
            self.checks[key]['icon'].color = "blue"
        elif status == 'success':
            self.checks[key]['icon'].name = ft.Icons.CHECK_CIRCLE
            self.checks[key]['icon'].color = "green"
        elif status == 'failed':
            self.checks[key]['icon'].name = ft.Icons.CANCEL
            self.checks[key]['icon'].color = "red"
        elif status == 'pending':
            self.checks[key]['icon'].name = ft.Icons.CIRCLE_OUTLINED
            self.checks[key]['icon'].color = "grey"

        self.checks[key]['status'] = status
        self.page.update()

    def start_initial_check(self):
        """Start checking dependencies"""
        def check_thread():
            self.status_text.value = "Tizim tekshirilmoqda..."
            self.page.update()

            # Check Python
            self.update_check_status('python', 'checking')
            time.sleep(0.3)
            if sys.version_info >= (3, 7):
                self.update_check_status('python', 'success')
            else:
                self.update_check_status('python', 'failed')

            # Check Flet
            self.update_check_status('flet', 'checking')
            time.sleep(0.3)
            try:
                import flet
                self.update_check_status('flet', 'success')
            except ImportError:
                self.update_check_status('flet', 'failed')

            # Check yt-dlp
            self.update_check_status('yt_dlp', 'checking')
            time.sleep(0.3)
            try:
                import yt_dlp
                self.update_check_status('yt_dlp', 'success')
            except ImportError:
                self.update_check_status('yt_dlp', 'failed')

            # Check FFmpeg
            self.update_check_status('ffmpeg', 'checking')
            time.sleep(0.3)
            try:
                result = subprocess.run(['ffmpeg', '-version'],
                                      capture_output=True,
                                      timeout=5)
                if result.returncode == 0:
                    self.update_check_status('ffmpeg', 'success')
                else:
                    self.update_check_status('ffmpeg', 'failed')
            except:
                self.update_check_status('ffmpeg', 'failed')

            # Check if everything is OK
            all_ok = all(info['status'] == 'success' for info in self.checks.values())

            if all_ok:
                self.status_text.value = "✅ Barcha komponentlar tayyor!"
                self.status_text.color = "green"
                self.get_started_btn.visible = True
                self.setup_complete = True
            else:
                self.status_text.value = "⚠️ Ba'zi komponentlar o'rnatilmagan"
                self.status_text.color = "orange"
                self.install_btn.visible = True
                self.install_btn.disabled = False

            self.page.update()

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def install_dependencies(self, _e):
        """Install missing dependencies"""
        self.install_btn.disabled = True
        self.status_text.value = "O'rnatilmoqda, iltimos kuting..."
        self.status_text.color = "blue"
        self.page.update()

        def install_thread():
            # Install Python packages
            if self.checks['flet']['status'] != 'success' or self.checks['yt_dlp']['status'] != 'success':
                self.status_text.value = "Python kutubxonalari o'rnatilmoqda..."
                self.page.update()

                try:
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install', '--quiet',
                        'flet>=0.23.0', 'yt-dlp>=2024.0.0', 'ffmpeg-python>=0.2.0'
                    ])

                    self.update_check_status('flet', 'success')
                    self.update_check_status('yt_dlp', 'success')
                except:
                    self.status_text.value = "❌ Python kutubxonalarini o'rnatishda xatolik"
                    self.status_text.color = "red"
                    self.install_btn.disabled = False
                    self.page.update()
                    return

            # Install FFmpeg
            if self.checks['ffmpeg']['status'] != 'success':
                self.status_text.value = "FFmpeg o'rnatilmoqda..."
                self.page.update()

                system = platform.system()
                ffmpeg_installed = False

                try:
                    if system == "Darwin":  # macOS
                        # Check Homebrew
                        try:
                            subprocess.run(['brew', '--version'],
                                         capture_output=True,
                                         check=True)
                            subprocess.check_call(['brew', 'install', 'ffmpeg'],
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)
                            ffmpeg_installed = True
                        except:
                            pass
                    elif system == "Linux":
                        subprocess.check_call(['sudo', 'apt-get', 'update', '-qq'])
                        subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'],
                                            stdout=subprocess.DEVNULL)
                        ffmpeg_installed = True
                except:
                    pass

                if ffmpeg_installed:
                    self.update_check_status('ffmpeg', 'success')
                else:
                    self.status_text.value = "⚠️ FFmpeg o'rnatilmadi, lekin davom etish mumkin"
                    self.status_text.color = "orange"
                    self.page.update()
                    time.sleep(2)

            # Check if everything is OK now
            all_ok = all(info['status'] == 'success' for key, info in self.checks.items() if key != 'ffmpeg')

            if all_ok:
                self.status_text.value = "✅ O'rnatish muvaffaqiyatli tugadi!"
                self.status_text.color = "green"
                self.get_started_btn.visible = True
                self.install_btn.visible = False
                self.setup_complete = True
            else:
                self.status_text.value = "❌ Ba'zi komponentlarni o'rnatib bo'lmadi"
                self.status_text.color = "red"
                self.install_btn.disabled = False

            self.page.update()

        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()

    def start_app(self, _e):
        """Start the main app"""
        self.page.clean()

        # Show version selection in the same window
        def start_mvp(_e):
            self.page.clean()
            import youtube_downloader_mvp
            youtube_downloader_mvp.YouTubeDownloaderMVP(self.page)

        def start_advanced(_e):
            self.page.clean()
            import youtube_downloader_advanced
            youtube_downloader_advanced.YouTubeDownloaderAdvanced(self.page)

        def start_playlist(_e):
            self.page.clean()
            import youtube_playlist_downloader
            youtube_playlist_downloader.PlaylistDownloader(self.page)

        self.page.title = "YouTube Downloader - Versiya tanlash"
        self.page.window_width = 550
        self.page.window_height = 500

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("YouTube Downloader", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Versiyani tanlang", size=16, color="grey"),
                        ft.Divider(),
                        ft.ElevatedButton(
                            text="MVP Versiya",
                            on_click=start_mvp,
                            width=350,
                            height=60,
                        ),
                        ft.Text("Oddiy yuklash", size=12, color="grey", text_align=ft.TextAlign.CENTER),
                        ft.Divider(),
                        ft.ElevatedButton(
                            text="Advanced Versiya",
                            on_click=start_advanced,
                            width=350,
                            height=60,
                        ),
                        ft.Text("Sifat tanlash", size=12, color="grey", text_align=ft.TextAlign.CENTER),
                        ft.Divider(),
                        ft.ElevatedButton(
                            text="Playlist Downloader",
                            on_click=start_playlist,
                            width=350,
                            height=60,
                        ),
                        ft.Text("Playlist videolarini yuklash", size=12, color="grey", text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=40,
            )
        )


def main(page: ft.Page):
    SetupWindow(page)


if __name__ == "__main__":
    ft.app(target=main)
