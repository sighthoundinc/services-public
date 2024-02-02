#
# Sample SIO pipeline extension
#

import sys
import os
import json
import time
import glob
from PIL import Image


class SIOPlugin:
    # ===========================================================
    def __init__(self):
        print(f"Creating SIO extension")
        self.prefix = "unknown"
        self.outputFolder = None
        self.generatedFiles = []
        self.maxOutput = 10

    # ===========================================================
    def clearFolder(self, folderPath, ext):
        # Construct the path pattern to match all files in the folder
        filesPattern = os.path.join(folderPath, '*.'+ext)

        # Use glob to get a list of all file paths matching the pattern
        toDelete = glob.glob(filesPattern)

        # Iterate through the list and delete each file
        for fp in toDelete:
            try:
                os.remove(fp)
                print(f"Deleted: {fp}")
            except Exception as e:
                print(f"Error deleting {fp}: {e}")

    # ===========================================================
    # Remove old output
    def trimOutput(self):
        while len(self.generatedFiles) > self.maxOutput:
            toDelete = self.generatedFiles.pop(0)
            try:
                name = os.path.join(self.outputFolder, toDelete)
                print(f"Removing {name}")
                os.remove(name+".jpg")
                os.remove(name+".json")
            except:
                print(f"Failed to remove {name} jpg/json")

    # ===========================================================
    # Prepare the module using provided configuration
    def configure(self, configJsonPath):
        try:
            with open(configJsonPath) as configJsonFile:
                config = json.load(configJsonFile)
            self.prefix = config["prefix"]
            self.outputFolder = config["outputFolder"]
        except:
            print(f"Failed to load extension module configuration from {configJsonPath}")
            raise
        # Ensure a clean slate
        os.makedirs(self.outputFolder, exist_ok=True)
        self.clearFolder(self.outputFolder, "jpg")
        self.clearFolder(self.outputFolder, "json")
        print(f"Loaded extension {__name__}")

    # ===========================================================
    # Process the output - save the json and the image
    def process(self, tick, frameDataStr, frame):
        frameData = json.loads(frameDataStr)
        t = int(time.time()*1000)
        name = os.path.join(self.outputFolder, f'{t}-{tick}')

        w = int(frameData.get("frameDimensions", {}).get("w", None))
        h = int(frameData.get("frameDimensions", {}).get("h", None))
        if w and h:
            img = Image.frombuffer("RGB", (w, h), frame, 'raw')
            print(f"Saving data in {name}")
            img.save(name+".jpg")
            with open(name+".json", 'w') as file:
                file.write(frameDataStr)

        self.generatedFiles.append(name)
        self.trimOutput()

        # always return the (potentially filtered or modified) output
        return frameDataStr

    # ===========================================================
    # Finalize the module
    def finalize(self):
        print(f"{self.prefix} - Pipeline completed")
        # Ensure a clean slate
        self.clearFolder(self.outputFolder, "jpg")
        self.clearFolder(self.outputFolder, "json")
