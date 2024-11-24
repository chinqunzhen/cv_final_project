# app.py
from flask import Flask, render_template, request, jsonify
import requests
from pathlib import Path
import random
from api_request import fetch_traffic_data, process_traffic_images
from ultralytics import YOLO
import os
from pathlib import Path
app = Flask(__name__)

# Replace with your API endpoint
#API_BASE_URL = "https://your-backend-api.com/traffic"

# Define paths for models
model1_path = os.path.join('models', 'best.pt')  # Model 1
model2_path = os.path.join('models', 'best_front.pt')  # Model 2

# Load both models
model1 = YOLO(model1_path)
model2 = YOLO(model2_path)
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



from PIL import Image
import numpy as np

@app.route('/predict/<camera_id>', methods=['GET'])
def predict(camera_id):
    """
    Predict route using both models simultaneously.
    """
    # Define directories for traffic images and predictions
    image_dir = Path("static") / "traffic_images"
    save_dir = Path("static") / "predict"

    # Ensure the prediction directory exists
    save_dir.mkdir(parents=True, exist_ok=True)

    # Get all image files for the specified camera_id
    images = [str(img_file) for img_file in image_dir.glob(f"{camera_id}_*.jpg")]

    if not images:
        return jsonify({"status": "error", "message": f"No images found for Camera ID {camera_id}."}), 404

    # Perform inference using both models
    results_model1 = model1(images)
    results_model2 = model2(images)

    predictions = {"model1": [], "model2": []}
    image_urls = []  # To store predicted image URLs

    for result1, result2 in zip(results_model1, results_model2):
        # Process Model 1 predictions
        model1_info = {
            "image": result1.path,
            "predictions": []
        }
        if result1.boxes is not None and result1.probs is not None:
            for box, prob in zip(result1.boxes, result1.probs):
                model1_info["predictions"].append({
                    "label": result1.names[prob.argmax()],
                    "confidence": float(prob.max()),
                    "coordinates": box.tolist()
                })
        predictions["model1"].append(model1_info)

        # Process Model 2 predictions
        model2_info = {
            "image": result2.path,
            "predictions": []
        }
        if result2.boxes is not None and result2.probs is not None:
            for box, prob in zip(result2.boxes, result2.probs):
                model2_info["predictions"].append({
                    "label": result2.names[prob.argmax()],
                    "confidence": float(prob.max()),
                    "coordinates": box.tolist()
                })
        predictions["model2"].append(model2_info)

        # Plot and combine annotations from both models
        img_array1 = result1.plot() if hasattr(result1, 'plot') else None
        img_array2 = result2.plot() if hasattr(result2, 'plot') else None

        if img_array1 is not None and img_array2 is not None:
            # Combine Model 1 and Model 2 annotations visually
            img_array_combined = np.maximum(img_array1, img_array2)
        elif img_array1 is not None:
            img_array_combined = img_array1
        elif img_array2 is not None:
            img_array_combined = img_array2
        else:
            continue  # Skip if no images are generated

        # Convert to PIL image and save
        img = Image.fromarray(np.uint8(img_array_combined))
        result_path = Path(result1.path)  # Use Model 1's path for naming
        save_path = save_dir / f"{result_path.stem}_predicted_combined.jpg"
        img.save(save_path)

        # Add the saved image URL to the response
        image_urls.append(f"/static/predict/{save_path.name}")

    # Return predictions and image URLs
    return jsonify({
        "status": "success",
        "data": predictions,
        "image_urls": image_urls
    })


# Placeholder for API endpoint
API_BASE_URL = ""  # Or set to None

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
