import traceback
import time
import os

from collections import deque

class SIO:
    def __init__(self, mcp_client, sio_drawer, max_size=100) -> None:
        self.mcp_client = mcp_client
        self.sio_drawer = sio_drawer
        self.sio_cache = deque(maxlen=max_size)

    def callback(self, message):
        try:
            self.sio_cache.append(message)
            sourceId = message.get("sourceId", "unknown")
            analyticsTimestamp = message.get("analyticsTimestamp",0)
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analyticsTimestamp/1000))
            
            mediaEvents = message.get("mediaEvents", {})
            for event in mediaEvents:
                type = event.get("type", "unknown")
                msg = event.get("msg", "unknown")
                if type == "video_file_closed":
                    file_path = f"/tmp/sio/{sourceId}_{os.path.basename(msg)}"
                    print(f"Downloading video to {file_path}")
                    t0 = time.time()
                    self.mcp_client.download_video(sourceId, msg, file_path)
                    print(f"Finished downloading video to {file_path} in {time.time() - t0} seconds")
                    t0 = time.time()
                    self.sio_drawer.draw_sio_data_to_video(self.sio_cache, file_path, f"/tmp/sio/output_{sourceId}_{os.path.basename(msg)}")
                    print(f"Finished drawing video to /tmp/sio/output_{sourceId}_{os.path.basename(msg)} in {time.time() - t0} seconds")

        except Exception as e:
            print(f"Caught exception {e} handling callback")
            traceback.print_exc()
            