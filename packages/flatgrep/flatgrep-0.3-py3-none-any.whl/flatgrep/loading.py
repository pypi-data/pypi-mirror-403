import sys
import time
import threading
from itertools import cycle


class LoadingScreen:
    """A CLI loading screen with spinner animation."""

    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "dots2": [".", "..", "...", ".."],
        "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "box": ["▖", "▘", "▝", "▗"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
    }

    def __init__(self, message: str = "Loading", spinner: str = "dots", delay: float = 0.1):
        self.message = message
        self.delay = delay
        self.spinner = cycle(self.SPINNERS.get(spinner, self.SPINNERS["dots"]))
        self._stop_event = threading.Event()
        self._thread = None

    def _animate(self):
        while not self._stop_event.is_set():
            frame = next(self.spinner)
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            time.sleep(self.delay)

    def start(self):
        """Start the loading animation."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, final_message: str = None):
        """Stop the loading animation."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        # Clear the line
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        if final_message:
            print(final_message)
        sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def loading(message: str = "Loading", spinner: str = "dots", delay: float = 0.1):
    """Create a loading screen context manager."""
    return LoadingScreen(message, spinner, delay)


if __name__ == "__main__":
    # Demo of different spinners
    print("Loading screen demo:\n")

    for spinner_name in LoadingScreen.SPINNERS:
        with loading(f"Using '{spinner_name}' spinner", spinner=spinner_name):
            time.sleep(2)
        print(f"✓ {spinner_name} complete")

    print("\nAll demos complete!")
