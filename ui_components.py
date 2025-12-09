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
        self.show_file_btn = ft.ElevatedButton(
            "Show in Finder", 
            icon=ft.Icons.FOLDER,
            visible=False,
            style=ft.ButtonStyle(color="white", bgcolor="#333333"),
            on_click=None # To be set by parent
        )
        
        self.controls = [
            self.status_text,
            self.progress_bar,
            ft.Row([
                self.progress_text,
                self.show_file_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ]

    def start_download(self, message="Starting download..."):
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.progress_text.visible = True
        self.progress_text.value = "0%"
        self.status_text.visible = True
        self.status_text.value = message
        self.status_text.color = ft.Colors.BLUE_ACCENT
        self.show_file_btn.visible = False
        self.update()

    def update_progress(self, percent, text=None):
        self.progress_bar.value = percent
        if text:
            self.progress_text.value = text
        else:
            self.progress_text.value = f"{int(percent * 100)}%"
        self.update()

    def complete(self, message="Download Complete!", on_show_click=None):
        self.status_text.value = message
        self.status_text.color = ft.Colors.GREEN_ACCENT
        self.progress_bar.value = 1
        self.progress_text.value = "100%"
        if on_show_click:
            self.show_file_btn.on_click = on_show_click
            self.show_file_btn.visible = True
        self.update()

    def error(self, message):
        self.status_text.value = f"Error: {message}"
        self.status_text.color = ft.Colors.RED_ACCENT
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.update()

    def reset(self):
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.status_text.visible = False
        self.show_file_btn.visible = False
        self.update()
