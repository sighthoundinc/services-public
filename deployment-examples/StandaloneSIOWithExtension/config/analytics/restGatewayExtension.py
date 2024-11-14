#
# A sample extension to relay SIO output to REST API
# The operation is performed asynchronously, to avoid holding up the pipeline on possible server delays
#

import sys
import os
import json
import traceback
import time
import threading
import requests
import io
from PIL import Image


# ------------------------------------------------------------------------------------
# Plugin
#   - asynchronously POSTs SIO results to REST endpoint
#   - aggregates results from multiple frames
# ------------------------------------------------------------------------------------
class SIOPlugin:
    # -------------------------------------------------------------------------------
    def __init__(self):
        self.pendingOutputs = {}
        self.mutex = threading.Lock()
        self.data_event = threading.Event()
        self.finalized = False
        self.api_url = ""
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    # -------------------------------------------------------------------------------
    def postBatch(self, dataToPost):
        items = len(dataToPost)
        if items == 0:
            return
        files = {}

        # Loop through each buffer and JSON blob, and add them to files with unique keys
        for key in dataToPost:
            # Add the image file to the files dictionary with a unique name
            files[f'image_{key}'] = ('image.jpg', dataToPost[key][1], 'image/jpeg')
            # Add the JSON data as a text file to the files dictionary with a unique name
            files[f'json_{key}'] = (None, dataToPost[key][0], 'application/json')

        # Send the POST request
        print(f"Posting a batch of {items} outputs to {self.api_url}")
        if self.api_url:
            response = requests.post(self.api_url, files=files)

            # Print response
            if response.status_code != 200:
                print(f"Failed to upload series. Status code: {response.status_code}")
                print(response.text)


    # -------------------------------------------------------------------------------
    def run(self):
        while not self.finalized:
            self.data_event.wait()  # Wait for data to be deposited or stop signal
            self.mutex.acquire()
            dataToPost = self.pendingOutputs
            self.pendingOutputs = {}
            self.mutex.release()
            self.data_event.clear()  # Clear the event until new data arrives

            # POST the data
            self.postBatch(dataToPost)

    # -------------------------------------------------------------------------------
    # Methods each SIOPlugin has to implement
    # -------------------------------------------------------------------------------
    # Prepare the module using provided configuration
    def configure(self, configJsonPath):
        try:
            with open(configJsonPath) as configJsonFile:
                config = json.load(configJsonFile)
                self.api_url = config.get("restUri","")
        except:
            print(f"Failed to load extension module configuration from {configJsonPath}")
            raise

    # -------------------------------------------------------------------------------
    # Process the output
    def process(self, tick, frameDataStr, frame):
        if not frameDataStr:
            return frameDataStr

        try:
            message = json.loads(frameDataStr)
            w = int(message.get("frameDimensions", {}).get("w", "0"))
            h = int(message.get("frameDimensions", {}).get("h", "0"))

            # save the image to blob
            image = Image.frombytes("RGB", (w, h), frame)
            jpg_buffer = io.BytesIO()
            image.save(jpg_buffer, format="JPEG")
            jpg_buffer.seek(0)

            self.mutex.acquire()
            self.pendingOutputs[tick] = (frameDataStr, jpg_buffer)
            self.data_event.set()
            self.mutex.release()
        except:
            print(f"Exception - \n{traceback.format_exc()}")

        # always return the (potentially filtered or modified) output
        return frameDataStr

    # -------------------------------------------------------------------------------
    # Finalize the module
    def finalize(self):
        self.finalized = True
        self.data_event.set()       # Wake up the thread if it's waiting
        self.thread.join()           # Wait for the thread to finish
