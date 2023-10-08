import traceback
import time
import os

class SIO:
    def __init__(self, mcp_client, sio_drawer) -> None:
        self.mcp_client = mcp_client
        self.sio_drawer = sio_drawer
        self.seenLps = {}
        self.seenVehicles = {}
        self.memoryDepth = 10000

    # -------------------------------------------------------------------------------
    # Get box object
    # -------------------------------------------------------------------------------
    def getBox(self, obj):
        try:
            boxObj = obj["box"]
            box = [ boxObj["x"], boxObj["y"], boxObj["width"], boxObj["height"] ]
        except:
            box = [ 0, 0, 0, 0 ]
        return box

    # -------------------------------------------------------------------------------
    # Get object ID linked to the curent object
    # -------------------------------------------------------------------------------
    def getLinkedObjectId(self, obj, desiredObjType):
        id = None
        for link in obj.get("links", {}):
            if link.get("metaClass", None) == desiredObjType:
                id = link.get("id", None)
            if not id is None:
                break
        return id

    # -------------------------------------------------------------------------------
    # Get LP attributes
    # -------------------------------------------------------------------------------
    def getLPInfo(self, lps, lpKey):
        lp = lps[lpKey]
        lpString = lp.get("attributes", {}).get("lpString", {}).get("value", {})
        lpRegion = lp.get("attributes", {}).get("lpRegion", {}).get("value", {})
        lpBox = self.getBox(lp)

        # Find the linked vehicle, if any
        vehicleId = self.getLinkedObjectId(lp, "vehicles")

        return lpString, lpRegion, lpBox, vehicleId

    # -------------------------------------------------------------------------------
    # Get vehicle attributes
    # -------------------------------------------------------------------------------
    def getVehicleInfo(self, vehicles, vehicleId):
        vehicle = vehicles.get(vehicleId, {})
        makeModel = vehicle.get("attributes", {}).get("vehicleType", {}).get("value", "unknownMakeModel")
        color = vehicle.get("attributes", {}).get("color", {}).get("value", "unknownColor")
        vehicleBox = self.getBox(vehicle)
        return makeModel, color, vehicleBox

    # -------------------------------------------------------------------------------
    def cleanupMemory(self, currentTs):
        for key in list(self.seenLps.keys()):
            if currentTs - self.seenLps[key] > self.memoryDepth:
                del self.seenLps[key]
        for key in list(self.seenVehicles.keys()):
            if currentTs - self.seenVehicles[key] > self.memoryDepth:
                del self.seenVehicles[key]

    # -------------------------------------------------------------------------------
    # Get image ID associated with current message or None
    # -------------------------------------------------------------------------------
    def getFrameImageID(self, message):
        mediaEvents = message.get("mediaEvents", {})
        for event in mediaEvents:
            if event.get("type", None) == "image":
                return event.get("msg", None)
        return None

    # -------------------------------------------------------------------------------
    # Get image associated with current message or None
    # -------------------------------------------------------------------------------
    def getFrameImage(self, sourceId, message):
        image = None
        imageId = ""
        try:
            imageId = self.getFrameImageID(message)
            if imageId:
                image = self.mcp_client.get_image(sourceId, imageId)
        except Exception as e:
            print(f"Caught exception {e} handling callback with message {str(message)}")
            traceback.print_exc()

        return image

    # -------------------------------------------------------------------------------
    def parseSIOMessage(self, message):
        sourceId = message.get("sourceId", "unknown")
        frameTimestamp = message.get("frameTimestamp",0)
        frameTimestampValue = int(frameTimestamp)
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(frameTimestamp/1000))
        # print (f"Received message from source {sourceId} at {timestamp_str}")

        mc = message.get("metaClasses", {})
        lps = mc.get("licensePlates", {})
        vehicles = mc.get("vehicles", {})
        processedVehicles = []

        # Get image associated with the frame (this isn't guaranteed)
        frameImage = self.getFrameImage(sourceId, message)

        # Process license plates
        for lpKey in lps.keys():
            status = "Got"
            if lpKey in self.seenLps:
                status = "Improved"
            self.seenLps[lpKey] = frameTimestampValue

            lpString, lpRegion, lpBox, vehicleId = self.getLPInfo(lps, lpKey)

            # Process vehicle associated with LP (if found)
            if vehicleId:
                makeModel, color, vehicleBox = self.getVehicleInfo(vehicles, vehicleId)
                if vehicleId in self.seenVehicles:
                    status = "Improved"
                self.seenVehicles[vehicleId] = frameTimestampValue
                processedVehicles.append(vehicleId)
                print(f"{timestamp_str} - [{sourceId}] {status} {color} {makeModel} at {str(vehicleBox)} with LP {lpString} - {lpRegion}")
            else:
                print(f"{timestamp_str} - [{sourceId}] {status} LP: {lpString} - {lpRegion} at {str(lpBox)}")

        # Process those vehicles without associated license plates
        for vehicleId in vehicles.keys():
            lpId = self.getLinkedObjectId(vehicles.get(vehicleId,{}), "licensePlates")
            if lpId is None:
                # No link to an LP
                status = "Got"
                if vehicleId in self.seenVehicles:
                    status = "Improved"
                self.seenVehicles[vehicleId] = frameTimestampValue
                makeModel, color, vehicleBox = self.getVehicleInfo(vehicles, vehicleId)
                print(f"{timestamp_str} - [{sourceId}] {status} {color} {makeModel} at {str(vehicleBox)}")

        # TODO: demonstrate crops creation from the image we retrieved

        self.cleanupMemory(frameTimestampValue)

    # -------------------------------------------------------------------------------
    def callback(self, message):
        try:
            self.parseSIOMessage(message)
        except Exception as e:
            print(f"Caught exception {e} handling callback with message {str(message)}")
            traceback.print_exc()
