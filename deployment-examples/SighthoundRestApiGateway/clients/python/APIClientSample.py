import requests
import os
import base64


apiUrl = "http://localhost:8383/v11/images:annotate"
# Find the media file one level up
filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), "2lps.png")


# Convert input image to BASE64
with open(filename, "rb") as f:
    b64image = base64.b64encode(f.read())

# Compose the JSON request
batchRequest = {
    "requests": [
        {
            "image": {
                "content" : str(b64image, "utf-8")
            },
            "features": [
                {
                    "type": "VEHICLE_DETECTION"
                },
                {
                    "type": "LICENSE_PLATE_DETECTION"
                }
            ]
        }
    ]
}


# Submit the request
batchResponse = requests.post(apiUrl, json = batchRequest).json()


# Check for errors
if 'error' in batchResponse:
    print(f"Error: {str(batchResponse)}")
    exit(-1)

# Process the response
response = batchResponse['responses'][0]
print('Detected %r vehicles and %r license plates' %(
    len(response['vehicleAnnotations']),
    len(response['licenseplateAnnotations'])
))

print(f"Full response:\n=======\n{str(batchResponse)}")
