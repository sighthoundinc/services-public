import traceback
import time
import os

class SIOParser:
    def __init__(self) -> None:
        self.lps = {}

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
        makeModelScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("attributeScore", {})
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
    def parseSIOResult(self, result):
        frames = sorted([int(key) for key in result])
        for frame in frames:
            message = result[str(frame)]
            sourceId = message.get("sourceId", "unknown")
            frameTimestamp = message.get("frameTimestamp","0")

            mc = message.get("metaClasses", {})
            lps = mc.get("licensePlates", {})
            vehicles = mc.get("vehicles", {})

            # Process license plates
            for lpKey in lps.keys():
                links = lps[lpKey].get("links",{})[0]
                make = ""; model = ""; color = ""; vehicleBox = ""
                if "vehicles" == links.get("metaClass",{}):
                    vehicleId = links.get("id",{})
                    make, model, color, vehicleBox, makeModelScore = self.getVehicleInfo(vehicles, vehicleId)

                lpString, lpRegion, lpBox = self.getLPInfo(lps, lpKey)
                if lpKey in self.lps:
                    if self.lps[lpKey][3] == lpString and self.lps[lpKey][2] == lpRegion:
                        # Nothing changed about the plate (but the box may have gotten worse, so keep an earlier one)
                        continue

                self.onLicensePlate(sourceId, frame, lpKey, frameTimestamp, lpString,
                                    lpRegion, lpBox, make, model, color, makeModelScore, vehicleBox)


    # -------------------------------------------------------------------------------
    def onLicensePlate(self, sourceid, frameid, uid, frameTimestamp,
                       lpString, lpRegion, lpBox, make, model, color, makeModelScore, vehicleBox):
        frameTimestampValue = int(frameTimestamp)
        self.lps[uid] = ( sourceid, frameid, lpRegion, lpString, frameTimestamp, lpBox,
                         make, model, color, makeModelScore, vehicleBox )

    # -------------------------------------------------------------------------------
    def getLPs(self):
        res = []
        for k in self.lps:
            lp = self.lps[k]
            res.append( { 'time': lp[4], 'string' : lp[3], 'region' : lp[2], 'sourceId' : lp[0], 'box' : lp[5],
                          'oid' : k, 'frameid' : lp[1], 'make' : lp[6], 'model' : lp[7],  'color' : lp[8], 'vBox' : lp[9] } )
        return res
