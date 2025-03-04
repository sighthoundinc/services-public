import traceback
import time
import os
from Database import LicensePlateDB, LicensePlate

class SIO:
    def __init__(self, mcp_client, db_conf) -> None:
        self.mcp_client = mcp_client
        self.db_path = db_conf["path"]
        self.db = None

    # -------------------------------------------------------------------------------
    # DB connection needs to be created in same thread as the callback
    # -------------------------------------------------------------------------------
    def initDbConnection(self):
        self.db = LicensePlateDB(self.db_path)

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
    # Get LP attributes
    # -------------------------------------------------------------------------------
    def getLPInfo(self, lps, lpKey):
        lp = lps[lpKey]
        lpString = lp.get("attributes", {}).get("lpString", {}).get("value", {})
        lpRegion = lp.get("attributes", {}).get("lpRegion", {}).get("value", {})
        lpBox = self.getBox(lp)

        return lpString, lpRegion, lpBox

    # -------------------------------------------------------------------------------
    # Get Vehicle attributes
    # -------------------------------------------------------------------------------
    def getVehicleInfo(self, vehicles, vehicleKey):
        vehicle = vehicles[vehicleKey]
        makeModel = vehicle.get("attributes", {}).get("vehicleType", {}).get("value", {})
        makeModelScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("value", {})
        if isinstance(makeModel, dict):
            make = makeModel.get("make",{})
            model = makeModel.get("model",{}) + " " + makeModel.get("generation",{})
        else:
            make = makeModel
            model = ""
        color = vehicle.get("attributes", {}).get("color", {}).get("value", {})
        vehicleBox = self.getBox(vehicle)

        return make, model, color, vehicleBox, makeModelScore

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
    def parseSIOMessage(self, message):
        sourceId = message.get("sourceId", "unknown")
        frameTimestamp = message.get("frameTimestamp","0")

        mc = message.get("metaClasses", {})
        lps = mc.get("licensePlates", {})
        vehicles = mc.get("vehicles", {})

        # Get image associated with the frame (this isn't guaranteed)
        imageId = self.getFrameImageID(message)

        # Process license plates
        for lpKey in lps.keys():
            lpString, lpRegion, lpBox = self.getLPInfo(lps, lpKey)
            links = lps[lpKey].get("links",{})[0]
            make = ""; model = ""; color = ""; vehicleBox = ""
            if "vehicles" == links.get("metaClass",{}):
                vehicleId = links.get("id",{})
                make, model, color, vehicleBox, makeModelScore = self.getVehicleInfo(vehicles, vehicleId)

            self.onLicensePlate(sourceId, lpKey, frameTimestamp, lpString, lpRegion, lpBox,
                                make, model, color, makeModelScore, vehicleBox, imageId)


    # -------------------------------------------------------------------------------
    def onLicensePlate(self, sourceId, uid, frameTimestamp, lpString, lpRegion, lpBox, make, model, color, makeModelScore, vBox, imageId):
        frameTimestampValue = int(frameTimestamp)
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(frameTimestampValue/1000))

        lp = LicensePlate(uid, make, model, color, lpRegion, lpString, frameTimestamp, sourceId,
                          lpBox[0], lpBox[1], lpBox[2], lpBox[3], imageId)
        try:
            self.db.add_detection(lp)
            print(f"{timestamp_str} Got LP source={sourceId}, uid={uid} time={frameTimestamp} make={make} model={model} color={color} string={lpString} region={lpRegion} box={lpBox} imageId={imageId}")
        except:
            print(f"{timestamp_str} Failed to add to DB: source={sourceId}, uid={uid} time={frameTimestamp} string={lpString} region={lpRegion} box={lpBox}")
            print(f"Failed to insert/update LP: {traceback.format_exc()}")



    # -------------------------------------------------------------------------------
    def callback(self, message):
        try:
            self.parseSIOMessage(message)
        except Exception as e:
            print(f"Caught exception {e} handling callback with message {str(message)}")
            traceback.print_exc()
