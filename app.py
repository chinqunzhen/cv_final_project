# app.py
from flask import Flask, render_template, request, jsonify
import requests
from pathlib import Path
import random
from api_request import fetch_traffic_data, process_traffic_images
app = Flask(__name__)

# Replace with your API endpoint
#API_BASE_URL = "https://your-backend-api.com/traffic"

IMAGE_FOLDER = Path("traffic_images")  # Folder where images are stored



@app.route('/show_random_image')
def show_random_image():

    #IMAGE_FOLDER = Path("traffic_images")  # Define the image folder here

    # Get a list of all image files in the folder
    image_files = [f.name for f in IMAGE_FOLDER.glob("*.jpg")]

    if not image_files:
        return jsonify({"error": "No images found in the folder."}), 404

    # Select a random image
    random_image = random.choice(image_files)
    print(random_image)
    # Render the HTML template with the selected image filename
    return render_template("showimage.html", filename=random_image)


@app.route('/download_traffic_images')
def download_traffic_images():
    # Fetch traffic data from the API
    json_data = fetch_traffic_data()

    if json_data:
        # Print the JSON data to the console (for verification)
        print(json_data)

        # Process and download images from API (assuming this function exists in your code)
        process_traffic_images(json_data)

        # Fetch images from the local static folder
        image_dir = Path("static/traffic_images")
        image_data = []

        if image_dir.exists():
            for img_file in image_dir.glob("*.jpg"):
                # Extract camera ID from filename (assuming filename format: cameraID_timestamp.jpg)
                camera_id = img_file.stem.split('_')[0]
                image_data.append({
                    "camera_id": camera_id,
                    "url": f"/static/traffic_images/{img_file.name}"
                })

        return jsonify({
            "status": "success",
            "message": "Images downloaded successfully",
            "data": {
                "json_data": json_data,
                "images": image_data
            }
        })
    else:
        return jsonify({"status": "error", "message": "Failed to fetch traffic data"}), 500

@app.route('/')
def index():
    image_files = [f.name for f in IMAGE_FOLDER.glob("*.jpg")]

    if not image_files:
        return jsonify({"error": "No images found in the folder."}), 404

    # Select a random image
    random_image = random.choice(image_files)
    print(random_image)
    return render_template('index.html', filename=random_image)

@app.route('/get_traffic', methods=['POST'])
def get_traffic():
    expressway = request.json.get('expressway')
    try:
        # Fetch traffic data from the external API
        response = requests.get(f"{API_BASE_URL}?expressway={expressway}")
        data = response.json()
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({"error": "Failed to retrieve traffic data"}), 500

if __name__ == '__main__':
    app.run(debug=True)
