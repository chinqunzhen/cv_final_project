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
    Predict route with selective model execution:
    - Camera IDs 1702 and 1705 use only Model 1.
    - All other camera IDs use both Model 1 and Model 2.
    """
    # Define directories for traffic images and predictions
    image_dir = Path("static") / "traffic_images"
    save_dir = Path("static") / "predict"

    # Clear the 'predict' directory by removing all files before saving new images
    for file in save_dir.glob("*"):
        if file.is_file():
            file.unlink()

    # Ensure the prediction directory exists
    save_dir.mkdir(parents=True, exist_ok=True)
    total_predictions = 0
    total_incoming = 0

    # Get all image files for the specified camera_id
    images = [str(img_file) for img_file in image_dir.glob(f"{camera_id}_*.jpg")]

    if not images:
        return jsonify({"status": "error", "message": f"No images found for Camera ID {camera_id}."}), 404

    # Check if this is a specific camera ID that only uses Model 1
    specific_camera_ids = ["7794", "7793", "3795"]
    is_specific_camera = camera_id in specific_camera_ids

    predictions = {"model1": [], "model2": []}
    image_urls = []  # To store predicted image URLs

    # Perform inference using Model 1
    results_model1 = model1(images)

    for result1 in results_model1:
        # Process Model 1 predictions (cars)
        model1_info = {
            "image": result1.path,
            "predictions": []
        }
        total_predictions = len(result1.boxes)
        if result1.boxes is not None and result1.probs is not None:
            for box, prob in zip(result1.boxes, result1.probs):
                model1_info["predictions"].append({
                    "label": result1.names[prob.argmax()],
                    "confidence": float(prob.max()),
                    "coordinates": box.tolist()
                })

        predictions["model1"].append(model1_info)

        # Plot and save Model 1 (cars) predictions
        img_array1 = result1.plot() if hasattr(result1, 'plot') else None
        if img_array1 is not None:
            img1 = Image.fromarray(np.uint8(img_array1))
            result_path1 = Path(result1.path)  # Use Model 1's path for naming
            save_path1 = save_dir / f"{result_path1.stem}_predicted_model1.jpg"
            img1.save(save_path1)  # Save the image
            image_urls.append(f"/static/predict/{save_path1.name}")
        else:
            print(f"Error: Model 1 plot not available for {result1.path}")

    # If not a specific camera, perform inference using Model 2
    if not is_specific_camera:
        results_model2 = model2(images)
        for result2 in results_model2:
            # Process Model 2 predictions (incoming)
            model2_info = {
                "image": result2.path,
                "predictions": []
            }
            total_incoming = len(result2.boxes)
            if result2.boxes is not None and result2.probs is not None:
                for box, prob in zip(result2.boxes, result2.probs):
                    model2_info["predictions"].append({
                        "label": result2.names[prob.argmax()],
                        "confidence": float(prob.max()),
                        "coordinates": box.tolist()
                    })

            predictions["model2"].append(model2_info)

            # Plot and save Model 2 (incoming) predictions
            img_array2 = result2.plot() if hasattr(result2, 'plot') else None
            if img_array2 is not None:
                img2 = Image.fromarray(np.uint8(img_array2))
                result_path2 = Path(result2.path)  # Use Model 2's path for naming
                save_path2 = save_dir / f"{result_path2.stem}_predicted_model2.jpg"
                img2.save(save_path2)  # Save the image
                image_urls.append(f"/static/predict/{save_path2.name}")
            else:
                print(f"Error: Model 2 plot not available for {result2.path}")

    # Return predictions and image URLs
    return jsonify({
        "status": "success",
        "data": predictions,
        "image_urls": image_urls,
        "total_predictions": total_predictions,
        "total_incoming": total_incoming
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
