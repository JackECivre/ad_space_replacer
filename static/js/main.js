let hoverRect = null, lockedRect = null;
let zoomFactor = 1, scaleFactorX = 1, scaleFactorY = 1;
let originalWidth = 0, originalHeight = 0; // Original screenshot dimensions

// Show status messages to the user
function showStatus(message, type = "info") {
    const statusDiv = document.getElementById("status");
    statusDiv.innerHTML = `<p class="${type}">${message}</p>`;
}

// Open the user-specified webpage and receive zoom factor
async function openWebpage() {
    const url = document.getElementById("url").value;
    if (!url) {
        showStatus("Please enter a valid URL.", "error");
        return;
    }

    showStatus("Opening webpage. Please wait...", "info");

    try {
        const response = await fetch('/open_webpage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();
        if (response.ok) {
            zoomFactor = data.zoomFactor || 1;
            console.log(`Zoom Factor Received: ${zoomFactor}`);
            showStatus(data.message, "success");
            document.getElementById("screenshot-btn").style.display = "inline-block";
        } else {
            showStatus(`Error: ${data.error}`, "error");
        }
    } catch (error) {
        console.error("Open Webpage Error:", error);
        showStatus("Failed to open webpage. Check backend logs.", "error");
    }
}

// Capture full-page screenshot and send dimensions
async function takeScreenshot() {
    showStatus("Capturing screenshot...", "info");

    try {
        const response = await fetch('/capture_screenshot', { method: 'POST' });
        const data = await response.json();

        if (data.path) {
            const screenshot = document.getElementById("screenshot");
            screenshot.src = `/${data.path}`;
            originalWidth = data.width;
            originalHeight = data.height;

            // Wait for the image to load to calculate scaling
            screenshot.onload = () => calculateScaleFactors();
            document.getElementById("hover-instructions").style.display = "block";
            document.getElementById("size-input").style.display = "block";
        } else {
            showStatus(`Error: ${data.error}`, "error");
        }
    } catch (error) {
        console.error("Screenshot Error:", error);
        showStatus("Failed to capture screenshot.", "error");
    }
}

// Calculate scaling factors based on original and displayed size
function calculateScaleFactors() {
    const screenshot = document.getElementById("screenshot");
    scaleFactorX = (screenshot.clientWidth * zoomFactor) / originalWidth;
    scaleFactorY = (screenshot.clientHeight * zoomFactor) / originalHeight;
    console.log(`Scale Factors - X: ${scaleFactorX}, Y: ${scaleFactorY}`);
}

// Show a transparent rectangle while hovering
function previewRectangle(event) {
    if (lockedRect) return;

    const rect = document.getElementById("hover-rectangle");
    const widthInput = parseInt(document.getElementById("rect-width").value) || 200;
    const heightInput = parseInt(document.getElementById("rect-height").value) || 100;

    // Adjust dimensions using zoom and scaling factors
    const scaledWidth = Math.round(widthInput  * scaleFactorX);
    const scaledHeight = Math.round(heightInput *  scaleFactorY);

    rect.style.left = `${event.offsetX}px`;
    rect.style.top = `${event.offsetY}px`;
    rect.style.width = `${scaledWidth}px`;
    rect.style.height = `${scaledHeight}px`;
    rect.style.display = "block";

    hoverRect = { x: event.offsetX, y: event.offsetY, width: scaledWidth, height: scaledHeight };
}

// Lock the rectangle when clicked
function lockRectangle() {
    if (!hoverRect) return;

    lockedRect = {
        x: Math.round(hoverRect.x / scaleFactorX * zoomFactor),
        y: Math.round(hoverRect.y / scaleFactorY * zoomFactor),
        width: Math.round(hoverRect.width / scaleFactorX * zoomFactor),
        height: Math.round(hoverRect.height / scaleFactorY * zoomFactor)
    };

    document.getElementById("upload-section").style.display = "block";
    document.getElementById("hover-rectangle").style.display = "none";
    showStatus(
        `Locked rectangle at (${lockedRect.x}, ${lockedRect.y}), size ${lockedRect.width}x${lockedRect.height}.`,
        "success"
    );
}

// Upload and replace the locked rectangle
async function uploadCreative() {
    const fileInput = document.getElementById("file").files[0];
    if (!fileInput || !lockedRect) {
        return showStatus("Please lock a rectangle and upload a file.", "error");
    }

    showStatus("Uploading creative...", "info");
    const formData = new FormData();
    formData.append("file", fileInput);
    Object.entries(lockedRect).forEach(([key, value]) => formData.append(key, value));

    try {
        const response = await fetch("/upload_creative", { method: "POST", body: formData });
        const data = await response.json();

        if (data.path) {
            document.getElementById("updated-image").src = `/${data.path}`;
            document.getElementById("download-link").href = "/download";
            document.getElementById("updated-container").style.display = "block";
            showStatus("Creative replaced successfully!", "success");
        } else {
            showStatus(`Error: ${data.error}`, "error");
        }
    } catch (error) {
        console.error("Upload Error:", error);
        showStatus("An error occurred while replacing the creative.", "error");
    }
}

// Reset application state
async function resetApp() {
    showStatus("Resetting the application...", "info");
    await fetch("/reset", { method: "POST" });
    window.location.reload();
}

// Initialize event listeners
document.getElementById("screenshot").addEventListener("mousemove", previewRectangle);
document.getElementById("screenshot").addEventListener("click", lockRectangle);
