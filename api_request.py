# -*- coding: utf-8 -*-

import json
import requests
from pathlib import Path
import concurrent.futures
import time
from datetime import datetime

#api = "https://api.data.gov.sg/v1/transport/traffic-images"
#response = requests.get(api)
#x = response.text
#print(x)

# JSON formatted string
#dictionary = json.loads(x)
#print(dictionary)
def fetch_traffic_data():
    # Define the API endpoint
    api = "https://api.data.gov.sg/v1/transport/traffic-images"  # Replace this URL with the actual API endpoint

    try:
        # Make a request to the API
        response = requests.get(api)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the response text as JSON
        json_data = response.json()

        print("Fetched traffic data:", json_data)  # Print the dictionary to console for debugging
        return json_data  # Return the dictionary

    except requests.exceptions.RequestException as e:
        print(f"Error fetching traffic data: {e}")
        return None
def download_image(camera_data, output_dir):
    """
    Download a single image from camera data and save it to the output directory.

    Args:
        camera_data (dict): Dictionary containing camera information
        output_dir (Path): Directory to save the images
    """
    try:
        # Extract information
        timestamp = camera_data['timestamp']
        image_url = camera_data['image']
        camera_id = camera_data['camera_id']

        # Convert timestamp to datetime for filename
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        filename = f"{camera_id}_{dt.strftime('%Y%m%d_%H%M%S')}.jpg"

        # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Save the image
        image_path = output_dir / filename
        with open(image_path, 'wb') as f:
            f.write(response.content)

        print(f"Successfully downloaded: {filename}")
        return True

    except Exception as e:
        print(f"Error downloading image from camera {camera_id}: {str(e)}")
        return False
def clear_directory(directory):
    """
    Remove all files in the specified directory.

    Args:
        directory (str): Path to the directory to clear.
    """
    # Ensure the directory exists
    path = Path(directory)
    if path.exists() and path.is_dir():
        for file in path.glob('*'):
            try:
                file.unlink()  # Remove file
                print(f"Deleted {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
def process_traffic_images(json_data, output_dir="static/traffic_images"):
    """
    Process and download all traffic camera images from the JSON data.

    Args:
        json_data (dict): Parsed JSON data containing camera information
        output_dir (str): Directory to save the images (will be created if it doesn't exist)
    """

    # Create output directory if it doesn't exist
    clear_directory(output_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract camera data
    cameras = json_data['items'][0]['cameras']

    # Download images using a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Create a list of futures
        future_to_camera = {
            executor.submit(download_image, camera, output_path): camera
            for camera in cameras
        }

        # Process completed downloads
        completed = 0
        failed = 0
        for future in concurrent.futures.as_completed(future_to_camera):
            if future.result():
                completed += 1
            else:
                failed += 1

    print(f"\nDownload Summary:")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Total: {len(cameras)}")

#process_traffic_images(dictionary)

