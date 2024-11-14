#
# Sample SIO pipeline extension
#

import sys
import os
import json
import traceback
import time
from PIL import Image

# ------------------------------------------------------------------------------------
# Tracked object
# ------------------------------------------------------------------------------------
class CombinedObject:
    # -------------------------------------------------------------------------------
    def __init__(self, owner, firstTimestamp, sourceId, frameSource):
        self.owner = owner
        self.sourceId = sourceId
        self.frameSource = frameSource
        self.lpId = None
        self.carId = None
        self.lpString = None
        self.lpStringScore = 0
        self.lpStringDetScore = 0
        self.lpStringTotalScore = 0
        self.makeModel = None
        self.makeModelScore = 0
        self.makeModelDetScore = 0
        self.makeModelTotalScore = 0
        self.color = None
        self.colorScore = 0
        self.colorDetScore = 0
        self.colorTotalScore = 0
        self.lpState = None
        self.lpStateScore = 0
        self.lpStateDetScore = 0
        self.lpStateTotalScore = 0
        self.timesReported = 0
        self.firstTimestamp = firstTimestamp
        self.lastSeenTimestamp = firstTimestamp
        self.lastUpdateTimestamp = firstTimestamp
        self.finalized = False

    # -------------------------------------------------------------------------------
    def duration(self):
        ret = self.lastSeenTimestamp - self.firstTimestamp
        return ret

    # -------------------------------------------------------------------------------
    def updateMMC(self, ts, carId, mm, mmScore, mmDetScore, mmTotalScore, color, colorScore, colorDetScore, colorTotalScore, useLastValue):
        if self.finalized:
            return False
        if carId != self.carId and self.carId:
            self.owner.log(f"updating car id {self.carId} with data for {carId}")
        updated = False
        self.carId = carId
        self.lastSeenTimestamp = ts
        if (mmTotalScore > self.makeModelTotalScore) or useLastValue:
            if self.makeModel != mm:
                self.makeModel = mm
                updated = True
            self.makeModelScore = mmScore
            self.makeModelDetScore = mmDetScore
            self.makeModelTotalScore = mmTotalScore
        if (colorTotalScore > self.colorTotalScore) or useLastValue:
            if self.color != color:
                self.color = color
                updated = True
            self.colorScore = colorScore
            self.colorDetScore = colorDetScore
            self.colorTotalScore = colorTotalScore

        if updated:
            self.lastUpdateTimestamp = ts
        return updated

    # -------------------------------------------------------------------------------
    def updateLP(self, ts, lpId, lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, lpState, lpStateScore, lpStateDetScore, lpStateTotalScore, useLastValue):
        if self.finalized:
            return False
        if lpId != self.lpId and self.lpId:
            self.owner.log(f"updating LP {self.lpId} with data for {lpId}")
        updated = False
        self.lpId = lpId
        self.lastSeenTimestamp = ts
        if (lpStringTotalScore > self.lpStringTotalScore) or useLastValue:
            if self.lpString != lpString:
                self.lpString = lpString
                updated = True
            self.lpStringScore = lpStringScore
            self.lpStringDetScore = lpStringDetScore
            self.lpStringTotalScore = lpStringTotalScore
        if (lpStateTotalScore > self.lpStateTotalScore) or useLastValue:
            if self.lpState != lpState:
                self.lpState = lpState
                updated = True
            self.lpStateScore = lpStateScore
            self.lpStateDetScore = lpStateDetScore
            self.lpStateTotalScore = lpStateTotalScore
        if updated:
            self.lastUpdateTimestamp = ts
        return updated

    # -------------------------------------------------------------------------------
    def formatVehicle(self):
        return f"Vehicle {self.carId} - {self.color} ({self.colorScore}/{self.colorDetScore}/{self.colorTotalScore}) {self.makeModel} ({self.makeModelScore}/{self.makeModelDetScore}/{self.makeModelTotalScore})"

    # -------------------------------------------------------------------------------
    def formatLP(self):
        return f"LP {self.lpId} - {self.lpString} ({self.lpStringScore}/{self.lpStringDetScore}/{self.lpStringTotalScore}) {self.lpState} ({self.lpStateScore}/{self.lpStateDetScore}/{self.lpStateTotalScore})"


    # -------------------------------------------------------------------------------
    def report(self, frameNum, timestampStr):
        status = "Got" if self.timesReported == 0 else "Changed"
        prefix = f"{timestampStr} - [{self.sourceId}-{self.frameSource}-{frameNum}] {status}"
        text = self.getReportString(prefix)
        self.timesReported += 1
        self.owner.log(f"{text}")

    # -------------------------------------------------------------------------------
    def finalReport(self):
        if self.finalized:
            return
        firstSeenStr = time.strftime('%H:%M:%S', time.gmtime(self.firstTimestamp/1000))
        lastSeenStr = time.strftime('%H:%M:%S', time.gmtime(self.lastSeenTimestamp/1000))
        prefix = f"{firstSeenStr}-{lastSeenStr} [{self.timesReported}] - [{self.sourceId}] - [{self.frameSource}] FINAL REPORT: "
        text = self.getReportString(prefix)
        self.owner.log(f"{text}")
        self.owner.onObjectTrackFinalized(self)
        self.finalized = True

    # -------------------------------------------------------------------------------
    def getReportString(self, prefix):
        if self.lpId and self.carId:
            text = f"{prefix} {self.formatVehicle()}; {self.formatLP()})"
        elif self.lpId:
            text = f"{prefix} {self.formatLP()})"
        elif self.carId:
            text = f"{prefix} {self.formatVehicle()} )"
        else:
            text = f"{prefix} Some kind of error ..."
        return text

    # -------------------------------------------------------------------------------
    def merge(self, other, ts):
        # We're merging two distinct tracks -- should use best, rather than last, value
        useLastValue = False
        self.updateMMC(ts, other.carId, other.makeModel, other.makeModelScore, other.makeModelDetScore, other.makeModelTotalScore, other.color, other.colorScore, other.colorDetScore, other.colorTotalScore, useLastValue)
        self.updateLP(ts, other.lpId,  other.lpString, other.lpStringScore, other.lpStringDetScore, other.lpStringTotalScore, other.lpState, other.lpStateScore, other.lpStateDetScore, other.lpStateTotalScore, useLastValue)
        self.firstTimestamp = min(self.firstTimestamp, other.firstTimestamp)

    # -------------------------------------------------------------------------------
    def updateBoth(self, ts, lpId, \
                    lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, \
                    lpState, lpStateScore, lpStateDetScore, lpStateTotalScore, \
                    useLastValueLP, carId, \
                    mm, mmScore, mmDetScore, mmTotalScore, \
                    color, colorScore, colorDetScore, colorTotalScore, \
                    useLastValueCar):
        updated = self.updateLP( ts, lpId, lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, lpState, lpStateScore, lpStateDetScore, lpStateTotalScore, useLastValueLP )
        updated = self.updateMMC( ts, carId, mm, mmScore, mmDetScore, mmTotalScore, color, colorScore, colorDetScore, colorTotalScore, useLastValueCar ) or updated
        return updated

# ------------------------------------------------------------------------------------
# Plugin
# ------------------------------------------------------------------------------------
class SIOPlugin:
    # -------------------------------------------------------------------------------
    def __init__(self) -> None:
        self.prefix = "unknown"
        # Combined objects we've seen
        self.seenObjects = {}
        self.memoryDepth = 10000
        self.onlyReportLPs = False
        self.outputFile = None
        self.jsonOutput = None
        self.outputCrops = None
        self.outputFrames = None
        self.maxTrackDuration = 0

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
        lpString = lp.get("attributes", {}).get("lpString", {}).get("value", "unknown")
        lpStringScore = lp.get("attributes", {}).get("lpString", {}).get("attributeScore", 0)
        lpStringDetScore = lp.get("attributes", {}).get("lpString", {}).get("detectionScore", 0)
        lpStringTotalScore = lp.get("attributes", {}).get("lpString", {}).get("totalScore", 0)
        lpRegion = lp.get("attributes", {}).get("lpRegion", {}).get("value", "unknown")
        lpRegionScore = lp.get("attributes", {}).get("lpRegion", {}).get("attributeScore", 0)
        lpRegionDetScore = lp.get("attributes", {}).get("lpRegion", {}).get("detectionScore", 0)
        lpRegionTotalScore = lp.get("attributes", {}).get("lpRegion", {}).get("totalScore", 0)

        lpBox = self.getBox(lp)

        # Find the linked vehicle, if any
        vehicleId = self.getLinkedObjectId(lp, "vehicles")

        return lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, lpRegion, lpRegionScore, lpRegionDetScore, lpRegionTotalScore, lpBox, vehicleId

    # -------------------------------------------------------------------------------
    # Get vehicle attributes
    # -------------------------------------------------------------------------------
    def getVehicleInfo(self, vehicles, vehicleId):
        vehicle = vehicles.get(vehicleId, {})
        makeModel = vehicle.get("attributes", {}).get("vehicleType", {}).get("value", "unknownMakeModel")
        makeModelScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("attributeScore", 0)
        makeModelDetScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("detectionScore", 0)
        makeModelTotalScore = vehicle.get("attributes", {}).get("vehicleType", {}).get("totalScore", 0)
        color = vehicle.get("attributes", {}).get("color", {}).get("value", "unknownColor")
        colorScore = vehicle.get("attributes", {}).get("color", {}).get("attributeScore", 0)
        colorDetScore = vehicle.get("attributes", {}).get("color", {}).get("detectionScore", 0)
        colorTotalScore = vehicle.get("attributes", {}).get("color", {}).get("totalScore", 0)
        vehicleBox = self.getBox(vehicle)
        return makeModel, makeModelScore, makeModelDetScore, makeModelTotalScore, color, colorScore, colorDetScore, colorTotalScore, vehicleBox

    # -------------------------------------------------------------------------------
    def processTrackedObjects(self, currentTs):
        for key in list(self.seenObjects.keys()):
            if currentTs - self.seenObjects[key].lastSeenTimestamp > self.memoryDepth:
                # This track has been gone for awhile, report (if we haven't yet) and remove
                self.seenObjects[key].finalReport()
                del self.seenObjects[key]
            elif self.maxTrackDuration > 0 and self.seenObjects[key].duration() >= self.maxTrackDuration:
                # Make final determination on track, but do not remove it
                self.seenObjects[key].finalReport()

    # -------------------------------------------------------------------------------
    def findVehicle(self, vehicleId):
        if vehicleId in self.seenObjects:
            return vehicleId
        for key in self.seenObjects:
            if self.seenObjects[key].carId == vehicleId:
                return key
        return None

    # -------------------------------------------------------------------------------
    def parseSIOMessage(self, frameNum, message, frame):
        sourceId = message.get("sourceId", "unknown")
        frameTimestamp = message.get("frameTimestamp",0)
        w = int(message.get("frameDimensions", {}).get("w", "0"))
        h = int(message.get("frameDimensions", {}).get("h", "0"))
        frameTimestampValue = int(frameTimestamp)
        timestamp_str = time.strftime('%H:%M:%S', time.gmtime(frameTimestamp/1000))
        frameSource = os.path.basename(message.get('frameSource',''))
        # print (f"Received message {str(message)} from source {sourceId} at {timestamp_str}")

        mc = message.get("metaClasses", {})
        lps = mc.get("licensePlates", {})
        vehicles = mc.get("vehicles", {})

        lpString = None
        lpStringScore = 0
        lpRegion = None
        lpRegionScore = 0
        lpBox = None
        vehicleId = None
        makeModel = None
        makeModelScore = 0
        makeModelDetScore = 0
        makeModelTotalScore = 0
        color = None
        colorScore = 0
        colorDetScore = 0
        colorTotalScore = 0
        vehicleBox = [ 0, 0, 0, 0 ]

        # Process license plates
        for lpKey in lps.keys():
            lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, lpRegion, lpRegionScore, lpRegionDetScore, lpRegionTotalScore, lpBox, vehicleId = self.getLPInfo(lps, lpKey)

            # Process vehicle associated with LP (if found)
            if vehicleId:
                makeModel, makeModelScore, makeModelDetScore, makeModelTotalScore, color, colorScore, colorDetScore, colorTotalScore, vehicleBox = self.getVehicleInfo(vehicles, vehicleId)

            # By default, trust pipeline updates
            updateLPWithLast = True
            updateCarWithLast = True

            if vehicleId and vehicleId in self.seenObjects and lpKey in self.seenObjects:
                # We have two distinct tracks (one LP, one car) merging here
                self.seenObjects[lpKey].merge(self.seenObjects[vehicleId], frameTimestampValue)
                objID = lpKey
                del self.seenObjects[vehicleId]
                # We're merging car track (which may have an older LP value), and LP track -- choose the best LP
                updateLPWithLast = False
            elif vehicleId and vehicleId in self.seenObjects:
                # It's an existing car track, but LP is new
                self.seenObjects[lpKey] = self.seenObjects[vehicleId]
                objID = lpKey
                del self.seenObjects[vehicleId]
            elif lpKey in self.seenObjects:
                # It's an existing LP track
                objID = lpKey
            else:
                # It's a branch new combination of vehicle and LP. This may also occur, if this vehicle was previously associated with a different LP, so check for that
                objID = None
                if vehicleId:
                    key = self.findVehicle(vehicleId)
                    if key:
                        # self.log(f"LP track {lpKey} and {key} are both associated with vehicle {vehicleId}")
                        objID = key
                        updateLPWithLast = False
                # if we haven't found an LP to replace, create new object
                if not objID:
                    objID = lpKey
                    self.seenObjects[lpKey] = CombinedObject(self, frameTimestamp, sourceId, frameSource)

            # Update the object, and report it if material update occurred
            if self.seenObjects[objID].updateBoth(frameTimestampValue, lpKey, \
                                                    lpString, lpStringScore, lpStringDetScore, lpStringTotalScore, \
                                                    lpRegion, lpRegionScore, lpRegionDetScore, lpRegionTotalScore, \
                                                    updateLPWithLast, vehicleId,  \
                                                    makeModel, makeModelScore, makeModelDetScore, makeModelTotalScore, \
                                                    color, colorScore, colorDetScore, colorTotalScore, \
                                                    updateCarWithLast):
                self.seenObjects[objID].report(frameNum, timestamp_str)
                self.saveImage(frame, frameNum, sourceId, lpString, lpBox, w, h)
                if vehicleId:
                    self.saveImage(frame, frameNum, sourceId, f"{makeModel}-{color}", vehicleBox, w, h)

        # Process those vehicles without associated license plates
        if not self.onlyReportLPs:
          for vehicleId in vehicles.keys():
              lpId = self.getLinkedObjectId(vehicles.get(vehicleId,{}), "licensePlates")
              if lpId is None:
                  # This vehicle has no associated LP, so it wasn't processed along with LPs
                    objID = None
                    key = self.findVehicle(vehicleId)
                    if key:
                        # self.log(f"LP track {key} was previously associated with vehicle {vehicleId}")
                        objID = key
                    # if we haven't found an LP to replace, create new object
                    if not objID:
                        objID = vehicleId
                        self.seenObjects[vehicleId] = CombinedObject(self, frameTimestamp, sourceId, frameSource)

                    makeModel, makeModelScore, makeModelDetScore, makeModelTotalScore, color, colorScore, colorDetScore, colorTotalScore, vehicleBox = self.getVehicleInfo(vehicles, vehicleId)
                    # Established track, trust pipeline updates
                    updateWithLastValue = True
                    if self.seenObjects[objID].updateMMC(frameTimestampValue, vehicleId, makeModel, makeModelScore, makeModelDetScore, makeModelTotalScore, color, colorScore, colorDetScore, colorTotalScore, updateWithLastValue):
                        self.seenObjects[objID].report(frameNum, timestamp_str)
                        self.saveImage(frame, frameNum, sourceId, f"{makeModel}-{color}", vehicleBox, w, h)

        # Finalize objects that haven't been updated in a while.
        # Similar logic may be employed to issue a final report on an object that has been tracked for a cetain period of time,
        # has been detected in a particular region, etc
        self.processTrackedObjects(frameTimestampValue)

    # -------------------------------------------------------------------------------
    def saveImage(self, frame, frameNum, sourceId, name, box, w, h):
        if box:
            if not self.outputCrops or w <= 0 or h <= 0:
                print("Not saving a crop")
                return
            location = self.outputCrops
        else:
            if not self.outputFrames:
                print("Not saving a frame")
                return
            location = self.outputFrames

        try:
            fn = os.path.join(location, sourceId + f"-{frameNum}-{name}.png")
            img = Image.frombuffer("RGB", (w, h), frame, 'raw')
            if box:
                x = int(box[0])
                y = int(box[1])
                w = int(box[2])
                h = int(box[3])
                cropped = img.crop((x,y,x+w,y+h))
            else:
                cropped = img
            cropped.save(fn)
        except:
            print(f"{traceback.format_exc()}")

    # -------------------------------------------------------------------------------
    def onObjectTrackFinalized(self, trackedObject):
        # A callback for final determintion on tracked object classification.
        # This is the place to open the gate, verify the LP against database or blacklist,
        # or perform any other application-specific routine needed
        pass

    # -------------------------------------------------------------------------------
    def log(self, msg):
        print(f"{msg}")
        if self.outputFile:
            self.outputFile.write(f"{msg}\n")
            self.outputFile.flush()

    # -------------------------------------------------------------------------------
    def ensureFolder(self, config, name):
        retval = config.get(name, '')
        if retval:
            try:
                os.makedirs( retval, exist_ok=True )
            except:
                print(f"Failed to create folder for {name} at {retval} - {traceback.format_exc()}")
                retval = None
        return retval

    # -------------------------------------------------------------------------------
    def openFile(self, config, name):
        retval = None
        fn = config.get(name, '')
        if fn:
            try:
                retval = open(fn, 'w')
            except:
                print(f"Failed to open file for {name} at {fn}")
                retval = None
        return retval


    # -------------------------------------------------------------------------------
    # Methods each SIOPlugin has to implement
    # -------------------------------------------------------------------------------
    # Prepare the module using provided configuration
    def configure(self, configJsonPath):
        try:
            with open(configJsonPath) as configJsonFile:
                config = json.load(configJsonFile)
                self.onlyReportLPs = config.get('onlyReportLPs', False)
                self.outputFile = self.openFile(config, 'outputFile')
                self.jsonOutput = self.openFile(config, 'jsonOutput')
                self.outputCrops = self.ensureFolder(config, 'outputCrops')
                self.outputFrames = self.ensureFolder(config, 'outputFrames')
                self.maxTrackDuration = config.get('maxTrackDuration', 0)
        except:
            print(f"Failed to load extension module configuration from {configJsonPath}")
            raise

    # -------------------------------------------------------------------------------
    # Process the output
    def process(self, tick, frameDataStr, frame):
        try:
            if not frameDataStr:
                return frameDataStr

            frameData = json.loads(frameDataStr)
            if self.jsonOutput:
                # Log current output, if requested by configuration
                j = { str(tick) : frameData }
                self.jsonOutput.write(f"{json.dumps(j, indent=4)}\n")
                self.jsonOutput.flush()
            self.parseSIOMessage( tick, frameData, frame )
        except:
            print(f"Exception - \n{traceback.format_exc()}")

        # always return the (potentially filtered or modified) output
        return frameDataStr

    # -------------------------------------------------------------------------------
    # Finalize the module
    def finalize(self):
        # Send final reports for objects still being updated
        for key in self.seenObjects:
            self.seenObjects[key].finalReport()
        # Close the output log file
        if self.outputFile:
            self.outputFile.close()
            self.outputFile = None
