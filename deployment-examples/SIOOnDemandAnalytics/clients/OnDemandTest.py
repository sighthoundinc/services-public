import os
import requests
import base64
import json
import time
import argparse
import copy
import traceback

def send_image_and_get_result(api_url, image_path, output_path):
    try:
        # Read the image binary
        with open(image_path, 'rb') as file:
            image_data = file.read()

        # Prepare the POST request with the image data
        jsonReq = {
            "id": 1,
            "imageData": base64.b64encode(image_data).decode('utf-8')
        }

        send_request_and_get_result(api_url, jsonReq, output_path)
    except Exception as e:
        print(f"Error: {str(e)}\n{traceback.format_exc()}")



def send_request_and_get_result(api_url, json_req, save_path):
    result = {}
    try:
        print(f"Sending request to {api_url}")
        start = time.time()
        if json_req:
            response = requests.post(api_url, json=json_req)
        else:
            response = requests.get(api_url, json=json_req)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response
            result = response.json()
            duration = time.time()-start

            print(f"JSON response in {duration}s:")
            if save_path:
                print(f"Saving response to {save_path}.json")
                with open(save_path+".json", 'w') as file:
                    file.write(json.dumps(result, indent=4))
                imgData = result.get("imageData", None)
                if not imgData:
                    imgData = result.get("streamDetail", [{}])[0].get("image", [{}])[0].get("imageData", None)
                if imgData:
                    print(f"Saving image to {save_path}.jpg")
                    with open(save_path+".jpg", 'wb') as file:
                        file.write(base64.b64decode(imgData))
            else:
                resultCopy = copy.deepcopy(result)
                imgData = resultCopy.get("imageData", None)
                if imgData:
                    resultCopy["imageData"] = "removedForBrevity"
                else:
                    imgData = resultCopy.get("streamDetail", [{}])[0].get("image", [{}])[0].get("imageData", None)
                    if imgData:
                        resultCopy["streamDetail"][0]["image"][0]["imageData"] = "removedForBrevity"
                print(json.dumps(resultCopy, indent=4))
        else:
            print(f"Error:{response.status_code}")
    except Exception as e:
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
    return result


def main():
    module_folder = os.path.dirname(os.path.abspath(__file__))

    # Create ArgumentParser object
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input', type=str, help='Path to the input file')
    parser.add_argument('-o', '--output', type=str, help='Path to the output file')
    args = parser.parse_args()

    # Access the values of the arguments
    image_path = args.input
    if not image_path:
        image_path = os.path.join( module_folder, "2lps.jpg" )


    api_url = 'http://127.0.0.1:8080/alpr'
    result = send_request_and_get_result(api_url, None, None)
    versions = result.get("version", None)
    if versions is None or len(versions) < 1:
        print(f"Unexpected result for {api_url}: {str(result)}")
        return
    version = versions[0]

    api_url = f'http://127.0.0.1:8080/alpr/{version}'
    result = send_request_and_get_result(api_url, None, None)
    resource = result.get("resource", [])
    if (not "locations" in resource) or \
       (not "analyzeImage" in resource) or \
       (not "annotateLive" in resource):
        print(f"Unexpected result for {api_url}: {str(result)} res={str(resource)}")
        return

    api_url = f'http://127.0.0.1:8080/alpr/{version}/analyzeImage'
    path = None if args.output is None else os.path.join (args.output, "analyzeImage")
    send_image_and_get_result(api_url, image_path, path)

    api_url = f'http://127.0.0.1:8080/alpr/{version}/locations'
    result = send_request_and_get_result(api_url, None, None)
    locations = result.get("location", [])
    location = locations[0].get('id', None) if locations and len(locations) >= 1 else None
    if not location:
        print(f"Unexpected result for {api_url}: {str(result)}")
        return

    api_url = f'http://127.0.0.1:8080/alpr/{version}/locations/{location}/streams'
    result = send_request_and_get_result(api_url, None, None)
    streams = result.get("stream", [])
    stream = streams[0].get('id', None) if streams and len(streams) >= 1 else None
    if stream is None:
        print(f"Unexpected result for {api_url}: {str(result)}")
        return

    api_url = f'http://127.0.0.1:8080/alpr/{version}/locations/{location}'
    path = None if args.output is None else os.path.join (args.output, "liveImage")
    result = send_request_and_get_result(api_url, None, path)

    api_url = f'http://127.0.0.1:8080/alpr/{version}/locations/{location}/annotateLive'
    path = None if args.output is None else os.path.join (args.output, "liveAnnotatedImage")
    result = send_request_and_get_result(api_url, None, path)


if __name__ == "__main__":
    main()

