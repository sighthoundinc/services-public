from flask import Flask, request, jsonify, make_response, send_file
import os
import time
import json
import base64
import traceback
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

app = Flask(__name__)

kVersion = "v1.0"
kLocationID = 100
kStreamID = 1
kLiveFolder = "/tmp/runvol/live"
kFwFolder = "/tmp/runvol/fw"
kTimeout = 2
kInvalidValue = "unknown"
kApiPrefix = '/alpr'
kLocation = 'location'
kLocations = kLocation + "s"
kStream = "stream"
kStreams = kStream + "s"
kAnalyzeImage = "analyzeImage"
kAnnotateLive = "annotateLive"

# -------------------------------------------------------------------------------
def getLinkedObjectId(obj, desiredObjType):
    id = None
    for link in obj.get("links", {}):
        if link.get("metaClass", None) == desiredObjType:
            id = link.get("id", None)
        if not id is None:
            break
    return id

# -------------------------------------------------------------------------------
def getLPInfo(lps, lpKey):
    lp = lps[lpKey]
    lpString = lp.get("attributes", {}).get("lpString", {}).get("value", None)
    lpStringScore = lp.get("attributes", {}).get("lpString", {}).get("attributeScore", 0)
    lpRegion = lp.get("attributes", {}).get("lpRegion", {}).get("value", None)
    lpRegionScore = lp.get("attributes", {}).get("lpRegion", {}).get("attributeScore", 0)

    # Find the linked vehicle, if any
    vehicleId = getLinkedObjectId(lp, "vehicles")

    return lpString, lpStringScore, lpRegion, lpRegionScore, vehicleId

# -------------------------------------------------------------------------------
def getVehicleInfo(vehicles, vehicleId):
    vehicle = vehicles.get(vehicleId, {})
    makeModel = vehicle.get("attributes", {}).get("vehicleType", {}).get("value", {})
    makeModelScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("attributeScore", 0)
    if isinstance(makeModel, dict):
        make = makeModel.get("make","unknown")
        model = makeModel.get("model","unknown") + " " + makeModel.get("generation","")
    else:
        make = makeModel
        model = "unknown"
    color = vehicle.get("attributes", {}).get("color", {}).get("value", "unknownColor")
    colorScore = vehicle.get("attributes", {}).get("color", {}).get("attributeScore", 0)
    return make, model, makeModelScore, color, colorScore



# -------------------------------------------------------------------------------
def parseSIOMessage(message):
    mc = message.get("metaClasses", {})
    lps = mc.get("licensePlates", {})
    vehicles = mc.get("vehicles", {})

    tuple = None
    tupleComplete = False

    # Process license plates
    for lpKey in lps.keys():
        lpString, lpStringScore, lpRegion, lpRegionScore, vehicleId = getLPInfo(lps, lpKey)

        # Process vehicle associated with LP (if found)
        if vehicleId:
            make, model, makeModelScore, color, colorScore = getVehicleInfo(vehicles, vehicleId)
        else:
            make = None
            model = None
            makeModelScore = 0
            color = None
            colorScore = 0

        newTuple = [ lpString, lpStringScore, lpRegion, lpRegionScore, make, model, makeModelScore, color, colorScore ]
        newTupleComplete = all(item is not None for item in newTuple)

        if not tuple or (newTupleComplete and not tupleComplete):
            tuple = newTuple

    if tuple is None:
        for vehicleId in vehicles.keys():
            make, model, makeModelScore, color, colorScore = getVehicleInfo(vehicles, vehicleId)
            if make and model and color:
                tuple = [ kInvalidValue, 0, kInvalidValue, 0, make, model, makeModelScore, color, colorScore ]

    if tuple is None:
        tuple = [ kInvalidValue, 0, kInvalidValue, 0, kInvalidValue, kInvalidValue, 0, kInvalidValue, 0 ]

    tuple = [ item if item is not None else kInvalidValue for item in tuple ]

    return tuple

### ======================================================
def convertJson(data, img):
    lpString, lpStringScore,  lpRegion, lpRegionScore, make, model, makeModelScore, color, colorScore = parseSIOMessage(data)

    res = {
        kLocation : {
            "id" : kLocationID
        },
        "streamDetail" : [ {
            kStream : {
                "id" : kStreamID
            },
            "preferredImage" : 1,
            "image" : [ {
                "id" : 1,
                "imageData" : img,
                "licensePlate" : {
                    "lpString" : lpString,
                    "lpStringScore" : lpStringScore,
                    "lpRegion" : lpRegion,
                    "lpRegionScore": lpRegionScore
                },
                "vehicle" : {
                    "make": make,
                    "model": model,
                    "makeModelScore": makeModelScore,
                    "color": color,
                    "colorScore": colorScore
                }
            } ]
        } ],
    }

    return jsonify(res)

### ======================================================
def loadJsonAndBase64(fn, loadImage=True):
    if not fn:
        return None, None
    data = None
    imageBase64 = None

    try:
        with open(fn, 'r') as file:
            data = json.load(file)
            # print(f"Loaded json from {fn} - {json.dumps(data)}")
        if loadImage:
            fnImg = fn.replace(".json", ".jpg")
            with open(fnImg, 'rb') as imageFile:
                imageData = imageFile.read()
                imageBase64 = base64.b64encode(imageData).decode('utf-8')
                # print(f"Loaded image from {fnImg}")
    except:
        print(f"Exception: {traceback.format_exc()}")
        pass

    if data is None or (imageBase64 is None and loadImage):
        # This will cause us to try an older file
        os.remove(fn)
    return data, imageBase64

### ======================================================
def mostRecentFileWithExtension(folderPath, extension):
    # Get a list of all files in the folder with the specified extension
    files = [os.path.join(folderPath, f) for f in os.listdir(folderPath) if f.endswith(extension) and os.path.isfile(os.path.join(folderPath, f))]

    if not files:
        print("No files found!")
        return None  # No files with the specified extension found

    # Find the most recent file based on the last modified time
    res = max(files, key=os.path.getmtime)
    return res

### ======================================================
def makeError(error_message, err=500):
    response = make_response(error_message, 500)
    response.headers['Content-Type'] = 'text/plain'
    return response

### ======================================================
@app.route(kApiPrefix, methods=['GET'])
def version():
    response = {
        'version': [ kVersion ]
    }
    return jsonify(response)

### ======================================================
@app.route(kApiPrefix + '/<string:version>', methods=['GET'])
def resource(version):
    response = {
        'resource': [ kLocations, kAnalyzeImage, kAnnotateLive ]
    }
    return jsonify(response)

### ======================================================
# Only one location is supported by this app
@app.route(kApiPrefix + '/<string:version>/' + kLocations, methods=['GET'])
def locations(version):
    response = {
        kLocation : [ {"id":kLocationID} ]
    }
    return jsonify(response)


### ======================================================
# Only one stream for one location is supported by this app
@app.route(kApiPrefix + '/<string:version>/' + kLocations + '/<string:location>/' + kStreams, methods=['GET'])
def streams(version, location):
    response = {
        kStream : [ {"id":kStreamID} ]
    }

    return jsonify(response)

### ======================================================
@app.route(kApiPrefix + '/<string:version>/' + kLocations + '/<string:location>', methods=['POST', 'GET'])
def capture(version, location):
    start = time.time()
    while True:
        fn = mostRecentFileWithExtension(kLiveFolder, ".json")
        json, base64image = loadJsonAndBase64(fn)
        response = convertJson(json, base64image)
        if response:
            return response
        if time.time() - start > kTimeout:
            break
        # Take a break for 50ms before trying again
        time.sleep(0.05)

    return makeError("Timeout trying to retrieve a live output")


### ======================================================
@app.route(kApiPrefix + '/<string:version>/' + kLocations + '/<string:location>/' + kAnnotateLive, methods=['POST', 'GET'])
def annotateLive(version, location):
    start = time.time()
    while True:
        fn = mostRecentFileWithExtension(kLiveFolder, ".json")
        json, base64image = loadJsonAndBase64(fn)

        if json and base64image:
            # Decode the base64 string
            imageData = base64.b64decode(base64image)

            # Create a BytesIO object from the decoded image data
            imageBytesio = BytesIO(imageData)

            # Create a PIL image from the BytesIO object
            image = Image.open(imageBytesio)
            draw = ImageDraw.Draw(image)
            textColor=(255,0,0)
            draw.text((5, 5), fn, fill=textColor, size=15)
            draw.text((5, 45), str(json), fill=textColor, size=15)

            outBytesio = BytesIO()
            image.save(outBytesio, format='JPEG')
            imageBytes = outBytesio.getvalue()

            imageBase64 = base64.b64encode(imageBytes).decode('utf-8')

            res = {
                "imageData" : imageBase64
            }

            return jsonify(res)


        if time.time() - start > kTimeout:
            break
        # Take a break for 50ms before trying again
        time.sleep(0.05)

    return makeError("Timeout trying to retrieve a live output")


### ======================================================
# Annotate a single image
@app.route(kApiPrefix + '/<string:version>/' + kAnalyzeImage, methods=['POST', 'GET'])
def analyzeImage(version):
    json = request.json
    if not 'imageData' in json:
        return makeError("Image data is missing")

    id = json.get('id', 0)
    image = json.get('imageData')

    # Decode the base64 data
    image_binary = base64.b64decode(image)

    # Write the binary data to a file
    fn = str(int(time.time()*1000))+str(id)+".jpg"
    fp = os.path.join(kFwFolder, fn)
    try:
        with open(fp, 'wb') as file:
            file.write(image_binary)
    except:
        return makeError(f"Failed to write the image to {fp}")

    fpResult = os.path.join(kFwFolder, "processed", fn+".json")

    start = time.time()
    while not os.path.isfile(fpResult):
        if time.time() - start > kTimeout:
            return makeError("Timeout trying to retrieve folder watcher output")
        # Take a break for 50ms before trying again
        time.sleep(0.05)

    jsonResult, _ = loadJsonAndBase64(fpResult, False)
    lpString, lpStringScore,  lpRegion, lpRegionScore, make, model, makeModelScore, color, colorScore = parseSIOMessage(data)

    # Clean up the result
    os.remove(fpResult)

    res = {
        "id" : id,
        "imageData" : image,
        "licensePlate" : {
            "lpString" : lpString,
            "lpStringScore" : lpStringScore,
            "lpRegion" : lpRegion,
            "lpRegionScore": lpRegionScore
        },
        "vehicle" : {
            "make": make,
            "model": model,
            "makeModelScore": makeModelScore,
            "color": color,
            "colorScore": colorScore
        }
    }

    return jsonify(res)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
