from flask import Flask, request, jsonify
from PIL import Image
import io
import os
import traceback

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    # Initialize lists to store results
    print(f"REQUEST!")
    results = []

    # Process each image and JSON pair in the form data
    for key in request.files:
        if key.startswith("image_"):
            # Extract the index from the image key (e.g., "image_0" -> 0)
            index = key.split("_")[1]
            json_key = f"json_{index}"

            # Get the image and JSON data
            image_file = request.files[key]
            json_data = request.form.get(json_key)

            if image_file and json_data:
                try:
                    # Open the image and process it (e.g., save or analyze)
                    image = Image.open(image_file)
                    # For demonstration, save the image (optional)
                    image.save(f"processed_image_{index}.jpg")

                    # Load and process JSON data
                    json_blob = request.get_json(silent=True)

                    # Simulate processing for demonstration
                    print(f"Processing image {index} with JSON data: {json_blob}")

                    # Append success result for this item
                    results.append({"index": index, "status": "success"})
                except Exception as e:
                    # Handle any processing errors
                    results.append({"index": index, "status": "error", "error": str(e)})
            else:
                results.append({"index": index, "status": "error", "error": "Missing image or JSON data"})

    return jsonify({"results": results})

if __name__ == '__main__':
    port = int(os.getenv("REST_PORT", 5000))
    host = os.getenv("REST_HOST", '0.0.0.0')
    app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", '/data/folder-watch-input')
    try:
        print(f"Running REST provider on {host}:{port}")
        app.run(host=host, port=port, debug=True)
    except:
        print(f"{traceback.format_exc()}")
        raise
