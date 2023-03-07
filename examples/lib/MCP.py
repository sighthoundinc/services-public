import requests
from PIL import Image
import numpy as np
from io import BytesIO
import time

class MCPClient:
    def __init__(self, conf):
        self.host = conf.get("host", "mcp")
        self.port = conf.get("port", 9097)
        self.user = conf.get("username", None)
        self.password = conf.get("password", None)
        print(f"mcp://{self.user}:{self.password}@{self.host}:{self.port}")
        
    # curl mcp:9097/hlsfs/source/<source_id>/segment/<image>
    def get_image(self, source_id, image):
        time.sleep(1)
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/segment/{image}"
        print("Downloading image from", url)

        if self.user and self.password:
            auth = (self.user, self.password)
        else:
            auth = None
        response = requests.get(url, auth=auth)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Image not found")
            elif response.status_code == 401:
                raise Exception("Unauthorized")
            else:
                raise Exception("Error downloading image", response.status_code)
        else:
            # Convert image to numpy array
            img = Image.open(BytesIO(response.content))
            arr = np.array(img)
            return arr

