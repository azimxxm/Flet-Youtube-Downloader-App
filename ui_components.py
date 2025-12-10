import flet as ft

class ProgressControl(ft.Column):
    def __init__(self, width=500):
        super().__init__()
        self.width = width
        self.spacing = 5
        
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

        self.cancel_btn = ft.ElevatedButton(
            "Cancel",
            icon=ft.Icons.CANCEL,
            color="white",
            bgcolor=ft.Colors.RED_600,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=10,
            ),
            visible=False,
            height=30,
            on_click=None # Set by parent
        )

        self.show_file_btn = ft.ElevatedButton(
            "Show in Finder", 
            icon=ft.Icons.FOLDER,
            visible=False,
            style=ft.ButtonStyle(color="white", bgcolor="#333333"),
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
