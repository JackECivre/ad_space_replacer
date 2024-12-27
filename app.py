import os

import requests
import sys
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory,url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from setup import create_folders, check_chromedriver

# Global driver
webdriver_instance = None

def get_base_dir():
    if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller bundle
        return os.path.join(sys._MEIPASS)
    return os.path.dirname(os.path.abspath(__file__))


# Update paths
base_dir = get_base_dir()
print(f"Base dir is : {base_dir}")
static_dir = os.path.join(base_dir, 'static')
SCREENSHOT_FOLDER = os.path.join(static_dir, 'screenshots')
UPDATED_FOLDER = os.path.join(static_dir,"updated")
CHROMEDRIVER_FOLDER = os.path.join(static_dir, "chromedriver")
CHROMEDRIVER_PATH = os.path.join(CHROMEDRIVER_FOLDER, "chromedriver.exe")

app = Flask(__name__, static_folder=os.path.join(base_dir, 'static'))

# Ensure folders exist
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
os.makedirs(UPDATED_FOLDER, exist_ok=True)
os.makedirs(CHROMEDRIVER_FOLDER, exist_ok=True)

def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/")
def index():
    """Serve the main HTML file."""
    reset()
    return send_from_directory("templates", "index.html")


@app.route('/open_webpage', methods=['POST'])
def open_webpage():
    """Open a webpage using Selenium and capture zoom factor."""
    global webdriver_instance
    try:
        data = request.get_json()
        url = data.get("url")
        print(f"Attempting to navigate to URL: {url}")

        if not url or not url.startswith(("http://", "https://")):
            print(f"Invalid URL provided: {url}")
            return jsonify({"error": "Invalid URL. Please provide a valid URL starting with http:// or https://"}), 400

        if webdriver_instance:
            webdriver_instance.quit()

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")

        print("Attempting to open Chrome with the following configuration:")
        print(f"ChromeDriver Path: {CHROMEDRIVER_PATH}")

        try:
            webdriver_instance = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
            print("Chrome opened successfully.")
        except Exception as e:
            print(f"Error initializing ChromeDriver: {e}")
            return jsonify({"error": f"Failed to initialize ChromeDriver: {e}"}), 500

        webdriver_instance.get(url)
        print(f"Navigated to URL: {url}")
        webdriver_instance.execute_script("document.body.requestFullscreen();")

        zoom_factor = webdriver_instance.execute_script("return window.devicePixelRatio;")
        print(f"Zoom Factor Detected: {zoom_factor}")

        return jsonify({
            "message": "Webpage opened successfully and set to full-screen. Scroll to the desired position and take a screenshot.",
            "zoomFactor": zoom_factor
        })
    except Exception as e:
        print(f"Error opening webpage: {e}")
        return jsonify({"error": f"Failed to open webpage: {str(e)}"}), 500


@app.route('/capture_screenshot', methods=['POST'])
def capture_screenshot():
    """Capture a full-page screenshot and close the Chrome window."""
    global webdriver_instance
    try:
        if not webdriver_instance:
            return jsonify({"error": "Webpage is not open yet."}), 400

        screenshot_path = os.path.join(SCREENSHOT_FOLDER, "full_page.png")
        print(f"Attempting to save screenshot to: {screenshot_path}")

        webdriver_instance.save_screenshot(screenshot_path)

        if not os.path.isfile(screenshot_path):
            print(f"Screenshot not created: {screenshot_path}")
            return jsonify({"error": "Screenshot could not be saved."}), 500

        img = Image.open(screenshot_path)
        width, height = img.size
        print(f"Screenshot Dimensions: {width}x{height}")

        webdriver_instance.quit()
        webdriver_instance = None

        return jsonify({
            "path": os.path.relpath(screenshot_path, start=os.getcwd()).replace("\\", "/"),
            "width": width,
            "height": height
        })
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/upload_creative', methods=['POST'])
def upload_creative():
    try:
        x = int(request.form['x'])
        y = int(request.form['y'])
        width = int(request.form['width'])
        height = int(request.form['height'])
        zoom_factor = float(request.form['zoomFactor'])
        creative_file = request.files['file']

        print(f"Received Rectangle (Before Zoom): x={x}, y={y}, width={width}, height={height}")
        print(f"Zoom Factor: {zoom_factor}")

        adjusted_x = int(x * zoom_factor) + 3
        adjusted_y = int(y * zoom_factor) + 3
        adjusted_width = int(width)
        adjusted_height = int(height)

        print(f"Adjusted Rectangle: x={adjusted_x}, y={adjusted_y}, width={adjusted_width}, height={adjusted_height}")

        screenshot_path = os.path.join(SCREENSHOT_FOLDER, "full_page.png")
        img = Image.open(screenshot_path)

        creative = Image.open(creative_file).resize((adjusted_width, adjusted_height), Image.Resampling.LANCZOS)

        img.paste(creative, (adjusted_x, adjusted_y), creative if creative.mode == "RGBA" else None)

        updated_path = os.path.join(UPDATED_FOLDER, "updated_image.png")
        img.save(updated_path)

        if not os.path.isfile(updated_path):
            print(f"Error: Updated image not created at {updated_path}")
            return jsonify({"error": "Failed to save updated image."}), 500

        print(f"Creative pasted at ({adjusted_x}, {adjusted_y}) with size ({adjusted_width}, {adjusted_height})")
        print(f"Updated image saved to: {updated_path}")

        return jsonify({"path": os.path.relpath(updated_path, start=os.getcwd()).replace("\\", "/")})
    except Exception as e:
        print(f"Error replacing creative: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/download')
def download_file():
    """Provide a download link for the updated image with a dynamic name."""
    try:
        file_path = os.path.join(UPDATED_FOLDER, "updated_image.png")
        if not os.path.isfile(file_path):
            print(f"File not found at {file_path}")
            return jsonify({"error": "File not found"}), 404

        # Extract information for the dynamic name
        uploaded_file_name = request.args.get('original_name', 'default_image')
        webpage_url = request.args.get('webpage_url', 'unknown_site')
        # Clean up the webpage address
        clean_webpage_url = webpage_url.replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]

        # Create the dynamic filename
        dynamic_filename = f"{uploaded_file_name}_{clean_webpage_url}.png"

        return send_from_directory(UPDATED_FOLDER, "updated_image.png", as_attachment=True,
                                   download_name=dynamic_filename)
    except Exception as e:
        print(f"Error in /download route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset():
    """Reset the app state and close the browser."""
    global webdriver_instance
    try:
        if webdriver_instance:
            webdriver_instance.quit()
        webdriver_instance = None

        for folder in [SCREENSHOT_FOLDER, UPDATED_FOLDER]:
            for file in os.listdir(folder):
                os.remove(os.path.join(folder, file))

        print("Application reset successfully.")
        return jsonify({"message": "Application reset successfully."})
    except Exception as e:
        print(f"Error resetting application: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/get_zoom_factor', methods=['GET'])
def get_zoom_factor():
    try:
        zoom_factor = webdriver_instance.execute_script("return window.devicePixelRatio;")
        return jsonify({"zoomFactor": float(zoom_factor)}), 200
    except Exception as e:
        print(f"Error fetching zoom factor: {e}")
        return jsonify({"error": str(e)}), 500


@app.after_request
def log_request(response):
    print(f"Request: {request.path} - Status: {response.status_code}")
    return response


@app.route('/static/screenshots/<filename>')
def serve_screenshot(filename):
    screenshot_path = os.path.join('static/screenshots', filename)
    if not os.path.exists(screenshot_path):
        print("Screenshot does not exist!")
    return send_from_directory('static/screenshots', filename)


if __name__ == "__main__":
    chromedriver_folder = create_folders()
    CHROMEDRIVER_PATH = check_chromedriver(chromedriver_folder)
    app.run(debug=True, port=5001)
