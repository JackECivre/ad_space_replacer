from flask import Flask, request, jsonify, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw
import os
import uuid

app = Flask(__name__)

# Paths
SCREENSHOT_FOLDER = "static/screenshots"
UPDATED_FOLDER = "static/updated"
CHROMEDRIVER_PATH = "d:\\chromedriver\\chromedriver.exe"

# Global driver
driver = None

# Ensure folders exist
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
os.makedirs(UPDATED_FOLDER, exist_ok=True)

@app.route("/")
def index():
    """Serve the main HTML file."""
    return send_from_directory("templates", "index.html")

@app.route('/open_webpage', methods=['POST'])
def open_webpage():
    """Open a webpage using Selenium and capture zoom factor."""
    global driver
    try:
        data = request.get_json()
        url = data.get("url")
        if not url:
            return jsonify({"error": "No URL provided."}), 400

        # Close any existing driver
        if driver:
            driver.quit()

        # Launch a new browser session
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
        driver.get(url)

        # Capture zoom factor
        zoom_factor = driver.execute_script("return window.devicePixelRatio;")
        print(f"Zoom Factor Detected: {zoom_factor}")

        return jsonify({
            "message": "Webpage opened successfully. Scroll to the desired position and take a screenshot.",
            "zoomFactor": zoom_factor
        })
    except Exception as e:
        print(f"Error opening webpage: {e}")
        return jsonify({"error": f"Failed to open webpage: {str(e)}"}), 500

@app.route('/capture_screenshot', methods=['POST'])
def capture_screenshot():
    """Capture a full-page screenshot and close the Chrome window."""
    global driver
    try:
        if not driver:
            return jsonify({"error": "Webpage is not open yet."}), 400

        # Save the screenshot
        screenshot_path = os.path.join(SCREENSHOT_FOLDER, "full_page.png")
        driver.save_screenshot(screenshot_path)

        # Get screenshot dimensions
        img = Image.open(screenshot_path)
        width, height = img.size
        print(f"Screenshot Dimensions: {width}x{height}")

        # Close the browser window after capturing the screenshot
        driver.quit()
        driver = None  # Reset the driver state

        return jsonify({
            "path": screenshot_path.replace("\\", "/"),
            "width": width,
            "height": height
        })
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/upload_creative', methods=['POST'])
def upload_creative():
    """Upload and replace a portion of the screenshot."""
    try:
        # Extract rectangle dimensions and file
        x = int(request.form['x'])
        y = int(request.form['y'])
        width = int(request.form['width'])
        height = int(request.form['height'])
        creative_file = request.files['file']

        if not creative_file:
            return jsonify({"error": "No file uploaded."}), 400

        # Load the original screenshot
        screenshot_path = os.path.join(SCREENSHOT_FOLDER, "full_page.png")
        if not os.path.exists(screenshot_path):
            return jsonify({"error": "Original screenshot not found."}), 400

        img = Image.open(screenshot_path)

        # Open and resize the creative
        creative = Image.open(creative_file)
        creative_resized = creative.resize((width, height), Image.Resampling.LANCZOS)

        # Replace the rectangle on the screenshot
        img.paste(creative_resized, (x, y))

        # Save the updated image
        updated_path = os.path.join(UPDATED_FOLDER, "updated_image.png")
        img.save(updated_path)
        print(f"Creative replaced and saved at: {updated_path}")

        return jsonify({"path": updated_path.replace("\\", "/")})
    except Exception as e:
        print(f"Error replacing creative: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download_file():
    """Provide a download link for the updated image."""
    return send_from_directory(UPDATED_FOLDER, "updated_image.png", as_attachment=True)

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the app state and close the browser."""
    global driver
    try:
        if driver:
            driver.quit()
        driver = None

        # Clear screenshots
        for folder in [SCREENSHOT_FOLDER, UPDATED_FOLDER]:
            for file in os.listdir(folder):
                os.remove(os.path.join(folder, file))

        print("Application reset successfully.")
        return jsonify({"message": "Application reset successfully."})
    except Exception as e:
        print(f"Error resetting application: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
