let hoverRect = null, lockedRect = null;
let zoomFactor = 1, scaleFactorX = 1, scaleFactorY = 1;
let originalWidth = 0, originalHeight = 0; // Original screenshot dimensions

// Show status messages to the user
function showStatus(message, type = "info") {
    const statusDiv = document.getElementById("status");
    statusDiv.innerHTML = `<p class="${type}">${message}</p>`;
}

async function updateZoomFactor() {
    try {
        const response = await fetch('/get_zoom_factor');
        const data = await response.json();

        if (response.ok) {
            zoomFactor = data.zoomFactor || 1;
            console.log(`Updated Zoom Factor: ${zoomFactor}`);
            showStatus("Zoom factor updated.", "success");
        } else {
            showStatus(`Error fetching zoom factor: ${data.error}`, "error");
        }
    } catch (error) {
        console.error("Zoom Factor Update Error:", error);
        showStatus("Failed to update zoom factor.", "error");
    }
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

// Example: Call this before capturing a screenshot
async function takeScreenshot() {
    await updateZoomFactor(); // Update zoom factor before taking a screenshot
    showStatus("Capturing screenshot...", "info");

    try {
        const response = await fetch('/capture_screenshot', { method: 'POST' });
        const data = await response.json();

        if (data.path) {
            const screenshot = document.getElementById("screenshot");
            screenshot.src = `/${data.path}?t=${new Date().getTime()}`;;
            originalWidth = data.width;
            originalHeight = data.height;

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
    const screenshot = document.getElementById("screenshot");
    const screenshotUrl = `/static/screenshots/full_page.png?t=${new Date().getTime()}`;
    document.getElementById("screenshot").src = screenshotUrl;
    console.log("Screenshot URL:", screenshotUrl);


    // Get image boundaries
    const imgRect = screenshot.getBoundingClientRect();

    // Calculate cursor position relative to the image
    const cursorX = event.clientX - imgRect.left;
    const cursorY = event.clientY - imgRect.top;

    const widthInput = parseInt(document.getElementById("rect-width").value) || 200;
    const heightInput = parseInt(document.getElementById("rect-height").value) || 100;

    // Adjust dimensions using scaling factors
    const scaledWidth = Math.round(widthInput * scaleFactorX);
    const scaledHeight = Math.round(heightInput * scaleFactorY);

    // Set rectangle properties
    rect.style.left = `${cursorX}px`;
    rect.style.top = `${cursorY}px`;
    rect.style.width = `${scaledWidth}px`;
    rect.style.height = `${scaledHeight}px`;
    rect.style.display = "block";

    // Update hoverRect with adjusted coordinates
    hoverRect = {
        x: cursorX,
        y: cursorY,
        width: scaledWidth+2,
        height: scaledHeight+2
    };
}

// Lock the rectangle when clicked
function lockRectangle(event) {
    const screenshot = document.getElementById("screenshot");
    const imgRect = screenshot.getBoundingClientRect();

    const lockedX = Math.round((event.clientX - imgRect.left) * (originalWidth / imgRect.width));
    const lockedY = Math.round((event.clientY - imgRect.top) * (originalHeight / imgRect.height));
    const widthInput = parseInt(document.getElementById("rect-width").value) || 200;
    const heightInput = parseInt(document.getElementById("rect-height").value) || 100;

    // Use zoomFactor for adjustments
    lockedRect = {
        x: Math.round(lockedX / zoomFactor),
        y: Math.round(lockedY / zoomFactor),
        width: Math.round(widthInput * zoomFactor),
        height: Math.round(heightInput * zoomFactor),
        zoomFactor: zoomFactor, // Ensure the correct zoom factor is attached
    };

    console.log("Locked Rectangle with Zoom Factor:", lockedRect);

    showStatus(
        `Rectangle locked at (${lockedRect.x}, ${lockedRect.y}), size ${lockedRect.width}x${lockedRect.height}, Zoom: ${zoomFactor}`,
        "success"
    );

    // Display the upload section
    document.getElementById("upload-section").style.display = "block";

    // Scroll to the upload section
    const uploadSection = document.getElementById("upload-section");
    uploadSection.scrollIntoView({ behavior: "smooth" }); // Smoothly scroll to the section
}

// Upload and replace the locked rectangle
async function uploadCreative() {
    const fileInput = document.getElementById("file");
    const formData = new FormData();

    if (!fileInput.files.length || !lockedRect) {
        showStatus("Please lock a rectangle and select a file before uploading.", "error");
        return;
    }

    const originalFileName = fileInput.files[0].name.split('.')[0]; // Get file name without extension
    const webpageUrl = document.getElementById("url").value;

    // Append locked rectangle details and zoom factor to the form data
    formData.append("x", lockedRect.x);
    formData.append("y", lockedRect.y);
    formData.append("width", lockedRect.width);
    formData.append("height", lockedRect.height);
    formData.append("zoomFactor", lockedRect.zoomFactor);
    formData.append("file", fileInput.files[0]);

    console.log("Sending Form Data:", {
        x: lockedRect.x,
        y: lockedRect.y,
        width: lockedRect.width,
        height: lockedRect.height,
        zoomFactor: lockedRect.zoomFactor,
    });

    // Send request to the backend
    try {
        const response = await fetch("/upload_creative", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (data.error) {
            console.error("Error:", data.error);
            showStatus("Error: " + data.error, "error");
        } else {
            console.log("Creative uploaded successfully:", data.path);
            showStatus("Creative uploaded successfully!", "success");

            // Display the updated image
            const updatedImage = document.getElementById("updated-image");
            updatedImage.src = `/static/updated/updated_image.png?t=${new Date().getTime()}`;


            document.getElementById("updated-container").style.display = "block";

            // Update the download link dynamically
            const downloadLink = document.getElementById("download-link");
            downloadLink.href = `/download?original_name=${encodeURIComponent(originalFileName)}&webpage_url=${encodeURIComponent(webpageUrl)}`;

            downloadLink.style.display = "inline-block"; // Show the download button

            // Move and show the restart button at the very bottom
            const restartButton = document.getElementById("restart-btn");
            restartButton.style.display = "inline-block"; // Ensure it's visible
            restartButton.style.marginTop = "20px"; // Add spacing
            restartButton.style.position = "relative"; // Ensure proper positioning
            restartButton.scrollIntoView({ behavior: "smooth" }); // Scroll to the button
        }
    } catch (error) {
        console.error("Upload Error:", error);
        showStatus("An error occurred while uploading the creative.", "error");
    }
}

function goBackToMarkRectangle() {
    // Reset the locked rectangle data
    lockedRect = null;

    // Clear the uploaded file input
    const fileInput = document.getElementById("file");
    fileInput.value = ""; // Reset the file input field

    // Hide the updated container
    document.getElementById("updated-container").style.display = "none";

    // Show instructions and size input for marking the rectangle
    document.getElementById("hover-instructions").style.display = "block";
    document.getElementById("size-input").style.display = "block";

    // Reset the hover rectangle display
    const hoverRectangle = document.getElementById("hover-rectangle");
    hoverRectangle.style.display = "none";

    // Clear any previous creative preview or updates
    const updatedImage = document.getElementById("updated-image");
    updatedImage.src = ""; // Clear the updated image

    const downloadLink = document.getElementById("download-link");
    downloadLink.href = "#"; // Reset the download link

    // Allow user to re-mark the rectangle
    showStatus("You can mark the rectangle again. Previous selection and uploaded creative cleared.", "info");
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