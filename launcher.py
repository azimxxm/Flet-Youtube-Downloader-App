import flet as ft
import subprocess
import sys
import os
import platform
import threading
import time
from pathlib import Path
from utils import get_responsive_dimensions
import youtube_downloader_mvp
import youtube_downloader_advanced
import youtube_playlist_downloader

# Add common paths to PATH for GUI app environment
common_paths = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin"
]
os.environ["PATH"] += os.pathsep + os.pathsep.join(common_paths)

# Setup complete flag file
SETUP_COMPLETE_FLAG = Path.home() / ".youtube_downloader_setup_complete"

class SetupWindow:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Downloader - Setup"

        # Set responsive dimensions based on screen size
        width, height = get_responsive_dimensions(page)
        self.page.window_width = width
        self.page.window_height = height

        # Load saved theme preference
        from ui_components import ThemeManager
        self.page.theme_mode = ThemeManager.get_theme()

        self.page.bgcolor = "#1a1a1a"
        self.page.padding = 0

        # Keyboard shortcuts
        self.page.on_keyboard_event = self.on_keyboard
        
        # Custom Fonts
        self.page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Inter")

        self.is_frozen = getattr(sys, 'frozen', False)

        self.checks = {
            'python': {'name': 'Python 3.7+', 'status': 'pending', 'icon': None},
            'flet': {'name': 'Flet Library', 'status': 'pending', 'icon': None},
            'yt_dlp': {'name': 'yt-dlp Library', 'status': 'pending', 'icon': None},
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

        # Define manual commands
        self.manual_commands = {
            'python': "brew install python",
            'flet': "pip install flet yt-dlp ffmpeg-python",
            'yt_dlp': "pip install yt-dlp",
            'ffmpeg': "brew install ffmpeg"
        }

        for key, info in self.checks.items():
            icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color="#666666", size=24)
            self.checks[key]['icon'] = icon
            
            # Command text for manual install (hidden by default)
            cmd_text = ft.TextField(
                value=self.manual_commands.get(key, ""),
                read_only=True,
                text_size=12,
                bgcolor="#1a1a1a",
                border_color="#444444",
                height=40,
                visible=False
            )
            self.checks[key]['cmd_text'] = cmd_text

            row = ft.Container(
                content=ft.Column([
                    ft.Row(
                        [
                            icon,
                            ft.Text(info['name'], size=16, color="white"),
                        ],
                        spacing=15,
                    ),
                    cmd_text
                ]),
                padding=10,
                bgcolor="#252525",
                border_radius=10,
            )
            self.check_items[key] = row
            check_list.controls.append(row)

        self.status_text = ft.Text("", size=14, color="#aaaaaa", text_align=ft.TextAlign.CENTER)

        self.install_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, color="white"),
                ft.Text("Install Dependencies", color="white"),
            ], spacing=10),
            on_click=self.install_dependencies,
            width=250,
            visible=False,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.BLUE_600, "hovered": ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
        )

        self.get_started_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.ARROW_FORWARD, color="white"),
                ft.Text("Get Started", color="white"),
            ], spacing=10),
            on_click=self.start_app,
            width=250,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor={"": ft.Colors.GREEN_600, "hovered": ft.Colors.GREEN_700},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
            ),
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Icon(ft.Icons.SETTINGS_SUGGEST, size=50, color=ft.Colors.BLUE_ACCENT),
                                            ft.Text("System Check", size=28, weight=ft.FontWeight.BOLD, color="white"),
                                            ft.Text("Verifying environment requirements...", size=14, color="#888888"),
                                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        padding=ft.Padding.only(bottom=20),
                                    ),
                                    check_list,
                                    ft.Container(height=20),
                                    self.status_text,
                                    ft.Container(height=10),
                                    ft.Row(
                                        [self.install_btn, self.get_started_btn],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                            padding=40,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_CENTER,
                                end=ft.Alignment.BOTTOM_CENTER,
                                colors=["#2d2d2d", "#1a1a1a"],
                            ),
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

    def update_check_status(self, key, status):
        """Update check status: pending, checking, success, failed"""
        if status == 'checking':
            self.checks[key]['icon'].name = ft.Icons.SYNC
            self.checks[key]['icon'].color = ft.Colors.BLUE_ACCENT
            self.checks[key]['icon'].animate_rotation = ft.Animation(1000, "linear")
            self.checks[key]['cmd_text'].visible = False
        elif status == 'success':
            self.checks[key]['icon'].name = ft.Icons.CHECK_CIRCLE
            self.checks[key]['icon'].color = ft.Colors.GREEN_ACCENT
            self.checks[key]['icon'].animate_rotation = None
            self.checks[key]['cmd_text'].visible = False
        elif status == 'failed':
            self.checks[key]['icon'].name = ft.Icons.CANCEL
            self.checks[key]['icon'].color = ft.Colors.RED_ACCENT
            self.checks[key]['icon'].animate_rotation = None
            self.checks[key]['cmd_text'].visible = True # Show manual command
        elif status == 'pending':
            self.checks[key]['icon'].name = ft.Icons.CIRCLE_OUTLINED
            self.checks[key]['icon'].color = "#666666"
            self.checks[key]['icon'].animate_rotation = None
            self.checks[key]['cmd_text'].visible = False

        self.checks[key]['status'] = status
        self.page.update()

    def start_initial_check(self):
        """Start checking dependencies"""
        def check_thread():
            self.status_text.value = "Checking system..."
            self.page.update()

            # If frozen (packaged app), assume Python and Libs are present
            if self.is_frozen:
                self.update_check_status('python', 'success')
                self.update_check_status('flet', 'success')
                self.update_check_status('yt_dlp', 'success')
            else:
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

            # Check FFmpeg (Always check this as it's external)
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
            except Exception:
                self.update_check_status('ffmpeg', 'failed')

            # Check if everything is OK
            all_ok = all(info['status'] == 'success' for info in self.checks.values())

            if all_ok:
                self.status_text.value = "✅ All systems operational!"
                self.status_text.color = ft.Colors.GREEN_ACCENT
                self.get_started_btn.visible = True
                self.setup_complete = True
                # Mark setup as complete
                SETUP_COMPLETE_FLAG.touch()
            else:
                self.status_text.value = "⚠️ Missing components detected"
                self.status_text.color = ft.Colors.ORANGE_ACCENT
                self.install_btn.visible = True
                self.install_btn.disabled = False

            self.page.update()

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def install_dependencies(self, _e):
        """Install missing dependencies"""
        self.install_btn.disabled = True
        self.status_text.value = "Installing dependencies..."
        self.status_text.color = ft.Colors.BLUE_ACCENT
        self.page.update()

        def install_thread():
            # Install Python packages (Only if not frozen)
            if not self.is_frozen:
                if self.checks['flet']['status'] != 'success' or self.checks['yt_dlp']['status'] != 'success':
                    self.status_text.value = "Installing Python libraries..."
                    self.page.update()

                    try:
                        subprocess.check_call([
                            sys.executable, '-m', 'pip', 'install', '--quiet',
                            'flet>=0.23.0', 'yt-dlp>=2024.0.0', 'ffmpeg-python>=0.2.0'
                        ])

                        self.update_check_status('flet', 'success')
                        self.update_check_status('yt_dlp', 'success')
                    except Exception:
                        self.status_text.value = "❌ Failed to install Python libraries"
                        self.status_text.color = ft.Colors.RED_ACCENT
                        self.install_btn.disabled = False
                        self.page.update()
                        return


            # Install FFmpeg
            if self.checks['ffmpeg']['status'] != 'success':
                self.status_text.value = "Installing FFmpeg..."
                self.page.update()

                system = platform.system()
                ffmpeg_installed = False

                try:
                    if system == "Darwin":  # macOS
                        # Check Homebrew
                        brew_path = "brew"
                        # Try to find brew in common locations if not in PATH
                        if not any(os.access(os.path.join(p, "brew"), os.X_OK) for p in os.environ["PATH"].split(os.pathsep)):
                             if os.path.exists("/opt/homebrew/bin/brew"):
                                 brew_path = "/opt/homebrew/bin/brew"
                             elif os.path.exists("/usr/local/bin/brew"):
                                 brew_path = "/usr/local/bin/brew"

                        try:
                            subprocess.run([brew_path, '--version'], capture_output=True, check=True)
                            subprocess.check_call([brew_path, 'install', 'ffmpeg'],
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)
                            ffmpeg_installed = True
                        except Exception as e:
                            print(f"Brew install failed: {e}")
                            pass
                    elif system == "Linux":
                        subprocess.check_call(['sudo', 'apt-get', 'update', '-qq'])
                        subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'],
                                            stdout=subprocess.DEVNULL)
                        ffmpeg_installed = True
                except Exception:
                    pass

                if ffmpeg_installed:
                    self.update_check_status('ffmpeg', 'success')
                else:
                    self.status_text.value = "⚠️ Could not install FFmpeg automatically. Please install it manually."
                    self.status_text.color = ft.Colors.ORANGE_ACCENT
                    self.page.update()
                    time.sleep(2)

            # Check if everything is OK now
            all_ok = all(info['status'] == 'success' for key, info in self.checks.items() if key != 'ffmpeg')

            if all_ok:
                self.status_text.value = "✅ Installation complete!"
                self.status_text.color = ft.Colors.GREEN_ACCENT
                self.get_started_btn.visible = True
                self.install_btn.visible = False
                self.setup_complete = True
                # Mark setup as complete
                SETUP_COMPLETE_FLAG.touch()
            else:
                self.status_text.value = "❌ Failed to install some components"
                self.status_text.color = ft.Colors.RED_ACCENT
                self.install_btn.disabled = False

            self.page.update()

        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()

    def start_app(self, _e):
        """Start the main app"""
        self.show_menu()

    def show_menu(self):
        """Show the mode selection menu"""
        self.page.clean()
        self.page.title = "Media Downloader - Select Platform"

        # Set responsive dimensions based on screen size
        width, height = get_responsive_dimensions(self.page)
        self.page.window_width = width
        self.page.window_height = height

        def go_back(_e=None):
            self.show_menu()

        # Show version selection in the same window
        def start_mvp(_e):
            self.page.clean()
            import youtube_downloader_mvp
            youtube_downloader_mvp.YouTubeDownloaderMVP(self.page, on_back=go_back)

        def start_advanced(_e):
            self.page.clean()
            import youtube_downloader_advanced
            youtube_downloader_advanced.YouTubeDownloaderAdvanced(self.page, on_back=go_back)

        def start_playlist(_e):
            self.page.clean()
            import youtube_playlist_downloader
            youtube_playlist_downloader.PlaylistDownloader(self.page, on_back=go_back)

        def start_instagram(_e):
            self.page.clean()
            import instagram_downloader
            instagram_downloader.InstagramDownloader(self.page, on_back=go_back)

        def create_option_card(title, description, icon, on_click, color):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text(description, size=12, color="#888888", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
                bgcolor="#252525",
                border_radius=15,
                border=ft.Border.all(1, "#333333"),
                on_click=on_click,
                ink=True,
                width=220,
                height=200,
                animate=ft.Animation(200, "easeOut"),
            )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Welcome to Media Downloader", size=32, weight=ft.FontWeight.BOLD, color="white"),
                                    ft.Text("Choose platform and download mode", size=16, color="#888888"),
                                    ft.Container(height=20),
                                    # Instagram Card (Featured)
                                    ft.Row(
                                        [
                                            create_option_card(
                                                "Instagram",
                                                "Download posts, reels & stories.",
                                                ft.Icons.CAMERA_ALT_ROUNDED,
                                                start_instagram,
                                                "#E4405F"
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    ft.Container(height=10),
                                    ft.Text("YouTube Modes", size=20, weight=ft.FontWeight.BOLD, color="white"),
                                    ft.Container(height=10),
                                    ft.Row(
                                        [
                                            create_option_card(
                                                "Simple",
                                                "Quick & easy download. Best for single videos.",
                                                ft.Icons.BOLT,
                                                start_mvp,
                                                ft.Colors.YELLOW_ACCENT
                                            ),
                                            create_option_card(
                                                "Advanced",
                                                "Choose quality, format & subtitles.",
                                                ft.Icons.TUNE,
                                                start_advanced,
                                                ft.Colors.RED_ACCENT
                                            ),
                                            create_option_card(
                                                "Playlist",
                                                "Download entire playlists at once.",
                                                ft.Icons.PLAYLIST_PLAY,
                                                start_playlist,
                                                ft.Colors.BLUE_ACCENT
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=20,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                            padding=40,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_CENTER,
                                end=ft.Alignment.BOTTOM_CENTER,
                                colors=["#2d2d2d", "#1a1a1a"],
                            ),
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

    def on_keyboard(self, e: ft.KeyboardEvent):
        import platform
        ctrl = e.ctrl or (e.meta and platform.system() == "Darwin")

        if ctrl and e.key.lower() == "t":
            # Toggle theme
            from ui_components import ThemeManager
            ThemeManager.toggle_theme(self.page)


def main(page: ft.Page):
    # Check if setup is already complete
    if SETUP_COMPLETE_FLAG.exists():
        # Skip setup and go directly to menu
        setup = SetupWindow(page)
        setup.show_menu()
    else:
        # Show setup window for first time
        SetupWindow(page)


if __name__ == "__main__":
    ft.run(main)
