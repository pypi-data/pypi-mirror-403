"""Welcome screen for Conviertlo"""
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container, VerticalScroll
from conviertlo.screens.file_browser_screen import FileBrowserScreen


class WelcomeScreen(Screen):
    """Initial landing screen with branding and file selection prompt"""

    CSS = """
    WelcomeScreen {
        background: $background;
    }

    #welcome-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #content {
        width: auto;
        height: auto;
    }

    .logo {
        color: $accent;
        text-align: center;
        text-style: bold;
        margin: 1 0;
    }

    .welcome-message {
        color: $foreground;
        text-align: center;
        margin: 1 0;
    }

    .prompt {
        color: $accent;
        text-align: center;
        margin: 2 0;
        text-style: bold;
    }

    .hotkey-hint {
        color: $secondary;
        text-align: center;
        margin: 1 0;
    }

    .dragdrop-hint {
        color: $foreground;
        text-align: center;
        margin: 1 0;
        text-style: italic;
    }
    """

    BINDINGS = [
        ("f", "open_file_browser", "Open File Browser"),
    ]

    def compose(self):
        """Compose the welcome screen"""
        
        ascii_logo = """
╔═══════════════════════════════════════╗
║                                       ║
║   ██████╗ ██████╗ ███╗   ██╗██╗   ██╗██╗███████╗██████╗ ████████╗██╗      ██████╗ 
║  ██╔════╝██╔═══██╗████╗  ██║██║   ██║██║██╔════╝██╔══██╗╚══██╔══╝██║     ██╔═══██╗
║  ██║     ██║   ██║██╔██╗ ██║██║   ██║██║█████╗  ██████╔╝   ██║   ██║     ██║   ██║
║  ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝██║██╔══╝  ██╔══██╗   ██║   ██║     ██║   ██║
║  ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝ ██║███████╗██║  ██║   ██║   ███████╗╚██████╔╝
║   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ 
║                                       ║
║        FFMPEG Copilot Converter       ║
║                                       ║
╚═══════════════════════════════════════╝
        """

        yield Container(
            Static(ascii_logo, classes="logo"),
            Static("Welcome to Conviertlo! 🎬", classes="welcome-message"),
            Static(
                "Convert and compress media files using natural language",
                classes="welcome-message"
            ),
            Static("Select files you want to convert...", classes="prompt"),
            Static("Press 'F' to open file browser", classes="hotkey-hint"),
            Static(
                "💡 Tip: You can drag and drop files directly (if supported)",
                classes="dragdrop-hint"
            ),
            id="welcome-container"
        )

    def action_open_file_browser(self):
        """Handle file browser opening action"""
        def handle_file_selection(selected_files):
            """Callback to handle selected files"""
            if selected_files:
                self.notify(f"Selected {len(selected_files)} file(s)")
                # Transition to instruction screen with selected files
                from conviertlo.screens.instruction_screen import InstructionScreen
                self.app.push_screen(InstructionScreen(
                    selected_files=selected_files,
                    copilot_service=self.app.copilot_service
                ))
            else:
                self.notify("File selection cancelled")
        
        # Push the file browser modal
        self.app.push_screen(FileBrowserScreen(), handle_file_selection)
