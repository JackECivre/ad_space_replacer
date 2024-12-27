import os
import platform
import sys
import json
from tkinter import Tk, filedialog

CONFIG_FILE = "chromedriver_config.json"


def create_folders():
    """Create necessary folders for the application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    folders = [
        os.path.join(static_dir, "screenshots"),
        os.path.join(static_dir, "updated"),
        os.path.join(static_dir, "chromedriver"),
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")
    return os.path.join(static_dir, "chromedriver")


def save_chromedriver_path(path):
    """Save the ChromeDriver path to a configuration file."""
    config = {"chromedriver_path": path}
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file)
    print(f"ChromeDriver path saved: {path}")


def load_chromedriver_path():
    """Load the ChromeDriver path from the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            config = json.load(config_file)
            return config.get("chromedriver_path")
    return None


def check_chromedriver(chromedriver_folder):
    """Check if ChromeDriver is present; guide the user to provide it if not."""
    saved_path = load_chromedriver_path()
    if saved_path and os.path.exists(saved_path):
        print(f"Using saved ChromeDriver path: {saved_path}")
        return saved_path

    chromedriver_path = os.path.join(chromedriver_folder, "chromedriver.exe")
    if os.path.exists(chromedriver_path):
        save_chromedriver_path(chromedriver_path)
        print("ChromeDriver is already present.")
        return chromedriver_path

    print("ChromeDriver not found.")
    print("Please select your ChromeDriver manually.")

    # Use a file dialog to select the ChromeDriver
    Tk().withdraw()  # Hide the root window
    selected_file = filedialog.askopenfilename(
        title="Select ChromeDriver",
        filetypes=[("Executable Files", "*.exe")],
    )

    if selected_file:
        save_chromedriver_path(selected_file)
        return selected_file
    else:
        print("No file selected. Exiting.")
        sys.exit("ChromeDriver is required to run this application.")


if __name__ == "__main__":
    chromedriver_folder = create_folders()
    check_chromedriver(chromedriver_folder)
