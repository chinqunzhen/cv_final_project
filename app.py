# app.py
from flask import Flask, render_template, request, jsonify
import requests
from pathlib import Path
import random
from api_request import fetch_traffic_data, process_traffic_images
app = Flask(__name__)

# Replace with your API endpoint
#API_BASE_URL = "https://your-backend-api.com/traffic"

IMAGE_FOLDER = Path("static/traffic_images")  # Folder where images are stored



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
    expressway = request.args.get('expressway')  # Capture the expressway parameter from the request
    json_data = fetch_traffic_data(expressway=expressway)  # Adjust fetch_traffic_data to accept this parameter

    if json_data:
        # Print the dictionary to the console (for verification)
        print(json_data)

        # Process and download images
        process_traffic_images(json_data)

        return jsonify({
            "status": "success",
            "message": "Images downloaded successfully",
            "data": json_data  # Include the dictionary in the response if needed
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
