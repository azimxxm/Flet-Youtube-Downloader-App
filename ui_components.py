import flet as ft
from pathlib import Path

class ProgressControl(ft.Column):
    def __init__(self, width=500, page=None):
        super().__init__()
        self.width = width
        self.spacing = 5
        self._page = page
        
        self.progress_bar = ft.ProgressBar(
            width=width, 
            visible=False, 
            color=ft.Colors.BLUE_ACCENT, 
            bgcolor="#444444",
            height=10,
            border_radius=5
        )
        self.progress_text = ft.Text("", visible=False, color="white", size=12)
        self.status_text = ft.Text("", visible=False, color="#aaaaaa", size=14)
        
        # Stats Row
        self.speed_text = ft.Text("", color="#888888", size=12)
        self.eta_text = ft.Text("", color="#888888", size=12)
        self.size_text = ft.Text("", color="#888888", size=12)
        
        self.stats_row = ft.Row(
            [self.size_text, self.speed_text, self.eta_text],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            visible=False
        )

        self.cancel_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.CANCEL, color="white"),
                ft.Text("Cancel", color="white"),
            ], spacing=8),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_600,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=10,
            ),
            visible=False,
            height=30,
            on_click=None # Set by parent
        )

        self.show_file_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER, color="white"),
                ft.Text("Show in Finder", color="white"),
            ], spacing=8),
            visible=False,
            style=ft.ButtonStyle(bgcolor="#333333"),
            on_click=None # To be set by parent
        )
        
        self.controls = [
            ft.Row([self.status_text, self.cancel_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.progress_bar,
            ft.Row([
                self.progress_text,
                self.show_file_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.stats_row
        ]

    def start_download(self, message="Starting download...", on_cancel=None):
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.progress_text.visible = True
        self.progress_text.value = "0%"
        self.status_text.visible = True
        self.status_text.value = message
        self.status_text.color = ft.Colors.BLUE_ACCENT
        self.show_file_btn.visible = False
        
        # Stats
        self.stats_row.visible = True
        self.speed_text.value = "Calculating..."
        self.eta_text.value = "--:--"
        self.size_text.value = "Size: --"
        
        if on_cancel:
            self.cancel_btn.visible = True
            self.cancel_btn.on_click = on_cancel
        else:
            self.cancel_btn.visible = False
            
        self.update()

    def update_progress(self, percent, text=None, speed=None, eta=None, size_info=None):
        async def do_update():
            self.progress_bar.value = percent
            if text:
                self.progress_text.value = text
            else:
                self.progress_text.value = f"{int(percent * 100)}%"

            if speed: self.speed_text.value = f"Speed: {speed}"
            if eta: self.eta_text.value = f"ETA: {eta}"
            if size_info: self.size_text.value = f"Size: {size_info}"

            self.update()

        if self._page:
            self._page.run_task(do_update)
        else:
            # Fallback for direct update
            self.progress_bar.value = percent
            if text:
                self.progress_text.value = text
            else:
                self.progress_text.value = f"{int(percent * 100)}%"

            if speed: self.speed_text.value = f"Speed: {speed}"
            if eta: self.eta_text.value = f"ETA: {eta}"
            if size_info: self.size_text.value = f"Size: {size_info}"

            self.update()

    def complete(self, message="Download Complete!", on_show_click=None):
        self.status_text.value = message
        self.status_text.color = ft.Colors.GREEN_ACCENT
        self.progress_bar.value = 1
        self.progress_text.value = "100%"
        self.cancel_btn.visible = False
        self.stats_row.visible = False
        
        if on_show_click:
            self.show_file_btn.on_click = on_show_click
            self.show_file_btn.visible = True
        self.update()

    def error(self, message):
        self.status_text.value = f"Error: {message}"
        self.status_text.color = ft.Colors.RED_ACCENT
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.cancel_btn.visible = False
        self.stats_row.visible = False
        self.update()
        
    def cancelled(self):
        self.status_text.value = "Download Cancelled"
        self.status_text.color = ft.Colors.ORANGE_ACCENT
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.cancel_btn.visible = False
        self.stats_row.visible = False
        self.update()

    def reset(self):
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.status_text.visible = False
        self.show_file_btn.visible = False
        self.cancel_btn.visible = False
        self.stats_row.visible = False
        self.update()


# ============================================================================
# REUSABLE UI COMPONENTS
# ============================================================================

class RadioOptionComponent(ft.Container):
    """Reusable radio option component for mode selection"""

    def __init__(self, label, value, icon, accent_color):
        super().__init__()
        self.content = ft.Row([
            ft.Radio(value=value, fill_color=accent_color),
            ft.Icon(icon, size=20, color="white"),
            ft.Text(label, color="white")
        ])
        self.bgcolor = "#252525"
        self.padding = 10
        self.border_radius = 10
        self.border = ft.Border.all(1, "#333333")


class HeaderComponent(ft.Container):
    """Reusable header component with title and optional buttons"""

    def __init__(self, title, icon, icon_color, show_back_button=False,
                 on_back=None, show_theme_toggle=False, on_theme_toggle=None):
        content_items = []

        if show_back_button and on_back:
            content_items.append(ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color="white",
                on_click=on_back,
                tooltip="Back to Menu"
            ))

        content_items.extend([
            ft.Icon(icon, size=32, color=icon_color),
            ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color="white"),
        ])

        if show_theme_toggle and on_theme_toggle:
            content_items.append(ft.IconButton(
                icon=ft.Icons.BRIGHTNESS_6,
                icon_color="white",
                on_click=on_theme_toggle,
                tooltip="Toggle Theme (Ctrl+T)"
            ))

        super().__init__()
        self.content = ft.Row(
            content_items,
            alignment=ft.MainAxisAlignment.CENTER if not show_back_button else ft.MainAxisAlignment.START,
        )
        self.padding = ft.Padding.only(top=20, bottom=15, left=20, right=20)
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#2d2d2d", "#1a1a1a"],
        )


class ThemeManager:
    """Manages theme persistence and switching across the application"""

    THEME_FILE = Path.home() / ".youtube_downloader_theme"

    @classmethod
    def get_theme(cls):
        """
        Get saved theme preference from file.

        Returns:
            ft.ThemeMode: DARK (default) or LIGHT
        """
        try:
            if cls.THEME_FILE.exists():
                theme = cls.THEME_FILE.read_text().strip()
                return ft.ThemeMode.LIGHT if theme == "light" else ft.ThemeMode.DARK
        except Exception:
            pass
        return ft.ThemeMode.DARK

    @classmethod
    def set_theme(cls, theme_mode):
        """
        Save theme preference to file.

        Args:
            theme_mode: ft.ThemeMode.DARK or ft.ThemeMode.LIGHT
        """
        try:
            theme_str = "light" if theme_mode == ft.ThemeMode.LIGHT else "dark"
            cls.THEME_FILE.write_text(theme_str)
        except Exception:
            pass

    @classmethod
    def toggle_theme(cls, page):
        """
        Toggle between dark and light theme and save preference.

        Args:
            page: Flet Page object

        Returns:
            ft.ThemeMode: New theme mode
        """
        new_theme = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.theme_mode = new_theme

        # Update background colors
        if new_theme == ft.ThemeMode.LIGHT:
            page.bgcolor = "#f5f5f5"
        else:
            page.bgcolor = "#1a1a1a"

        cls.set_theme(new_theme)
        page.update()
        return new_theme


class ProgressUpdateDebouncer:
    """
    Debounce progress updates to reduce UI lock contention during downloads.
    Updates only if: 5% progress change OR min_interval time elapsed.
    """

    def __init__(self, min_interval=0.1):
        """
        Initialize debouncer.

        Args:
            min_interval: Minimum seconds between updates (default 100ms)
        """
        self._last_update = 0
        self._min_interval = min_interval
        self._last_percent = 0

    def should_update(self, percent):
        """
        Check if progress update should be performed.

        Args:
            percent: Download progress (0.0 to 1.0)

        Returns:
            bool: True if update should be performed, False otherwise
        """
        import time
        current_time = time.time()
        percent_diff = abs(percent - self._last_percent)

        # Update if: 5% progress change OR min_interval elapsed
        if percent_diff >= 0.05 or (current_time - self._last_update) >= self._min_interval:
            self._last_update = current_time
            self._last_percent = percent
            return True
        return False

    def reset(self):
        """Reset debouncer state"""
        self._last_update = 0
        self._last_percent = 0
