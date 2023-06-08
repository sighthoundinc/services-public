import requests
from PIL import Image
import numpy as np
from io import BytesIO

class MCPClient:
    def __init__(self, conf):
        self.host = conf.get("host", "mcp")
        self.port = conf.get("port", 9097)
        self.user = conf.get("username", None)
        self.password = conf.get("password", None)
        if self.user and self.password:
            print(f"Connecting to mcp://{self.user}:*****@{self.host}:{self.port}")
        else:
            print(f"Connecting to mcp://{self.host}:{self.port}")

    def get(self, url):
        if self.user and self.password:
            auth = (self.user, self.password)
        else:
            auth = None
        response = requests.get(url, auth=auth)

        if response.status_code == 401:
                raise Exception("Unauthorized")
        else:
            return response

    # curl mcp:9097/hlsfs/source
    def list_sources(self):
        url = f"http://{self.host}:{self.port}/hlsfs/source"
        return self.get(url).json()

    # curl mcp:9097/hlsfs/source/<source_id>/stats
    def get_stats(self, source_id):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/stats"
        return self.get(url).json()

    # curl mcp:9097/hlsfs/source/<source_id>/image/<image>
    def get_image(self, source_id, image):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/image/{image}"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Image not found")
            else:
                raise Exception("Error downloading image", response.status_code)
        else:
            # Convert image to numpy array
            img = Image.open(BytesIO(response.content))
            arr = np.array(img)
            return arr

    # curl mcp:9097/hlsfs/source/<source_id>/segment/<video>
    def download_video(self, source_id, video, filepath):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/segment/{video}"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception(f"Video {video} not found for source {source_id}")
            else:
                raise Exception(f"Error downloading video {video} to {filepath} for source {source_id}", response.status_code)
        else:
            # Save image to file
            with open(filepath, 'wb') as f:
                f.write(response.content)

    # curl mcp:9097/hlsfs/source/<source_id>/segment/<segment>
    def get_segment(self, source_id, segment):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/segment/{segment}"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Segment not found")
            else:
                raise Exception("Error downloading Segment", response.status_code)
        else:
            return BytesIO(response.content)

    # curl mcp:9097/hlsfs/source/<source_id>/segment/<image>
    def download_image(self, source_id, image, filepath):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/segment/{image}"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Image not found")
            else:
                raise Exception("Error downloading image", response.status_code)
        else:
            # Save image to file
            with open(filepath, 'wb') as f:
                f.write(response.content)

    # curl mcp:9097/hlsfs/source/<source_id>/image
    def list_images(self, source_id):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/image"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Image not found")
            else:
                raise Exception("Error downloading image", response.status_code)
        else:
            return response.json()

    # curl mcp:9097/hlsfs/source/<source_id>/latest-image
    def get_latest_image(self, source_id):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/latest-image"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("Image not found")
            else:
                raise Exception("Error downloading image", response.status_code)
        else:
            # Convert image to numpy array
            img = Image.open(BytesIO(response.content))
            arr = np.array(img)
            return arr

    # curl mcp:9097/hlsfs/source/<source_id>/live
    def get_live_m3u8(self, source_id):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/live"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("M3U8 not found")
            else:
                raise Exception("Error downloading HLS", response.status_code)
        else:
            return response.text

    # curl mcp:9097/hlsfs/source/<source_id>/<start>..<end>.m3u8
    def get_m3u8(self, source_id, start, end):
        url = f"http://{self.host}:{self.port}/hlsfs/source/{source_id}/{start}..{end}.m3u8"
        response = self.get(url)

        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception("M3U8 not found:", url)
            else:
                raise Exception("Error downloading HLS:", url, ":", response.status_code)
        else:
            return response.text
        
    # curl mcp:9097/hlsfs/source/<source_id>/<start>..<end>.m3u8
    def get_m3u8_playlist(self, source_id, start, end):
        import m3u8
        m3u8_content = self.get_m3u8(source_id, start, end)
        # Remove all #EXT-UNIX-TIMESTAMP-MS lines from the m3u8 file
        # m3u8 library doesn't support this tag
        m3u8_content = '\n'.join([line for line in m3u8_content.split('\n') if not line.startswith("#EXT-UNIX-TIMESTAMP-MS")])
        return m3u8.loads(m3u8_content)


