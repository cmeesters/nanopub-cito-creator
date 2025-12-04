import wx
import sys
import argparse

# Try to detect curses availability dynamically
try:
    import curses  # noqa: F401
    HAS_CURSES = True
except Exception:
    HAS_CURSES = False

from ui.main_frame import MainFrame
from models.app_state import AppState

class CitoCreatorApp(wx.App):
    def __init__(self, app_state):
        self.app_state = app_state
        super().__init__(False)

    def OnInit(self):
        frame = MainFrame(None, self.app_state)
        frame.Show()
        return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='CiTO Creator - Generate citation nanopublications'
    )
    parser.add_argument(
        '--doi',
        type=str,
        help='DOI of the original paper to process'
    )
    parser.add_argument(
        '--test-server',
        action='store_true',
        help='Use nanopub test server instead of production'
    )
    parser.add_argument(
        '--auto-publish',
        action='store_true',
        help='Automatically publish nanopub without confirmation'
    )

    # Only expose --no-gui if curses is available
    if HAS_CURSES:
        parser.add_argument(
            '--no-gui',
            action='store_true',
            help='Run in terminal (curses) mode'
        )

    return parser.parse_args()

def main():
    args = parse_arguments()

    # Initialize application state
    app_state = AppState(
        initial_doi=args.doi,
        use_test_server=args.test_server,
        auto_publish=args.auto_publish
    )

    # If user asked for curses mode, run it
    if getattr(args, 'no-gui', False):
        if not HAS_CURSES:
            print("Curses is not available on this platform. Please use the GUI mode.")
            sys.exit(1)
        from cli.curses_cli import run_curses
        sys.exit(run_curses(app_state))

    # Launch GUI
    app = CitoCreatorApp(app_state)
    app.MainLoop()

if __name__ == "__main__":
    main()