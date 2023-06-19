import traceback
import time
import os

class SIO:
    def __init__(self, mcp_client, sio_drawer) -> None:
        self.mcp_client = mcp_client
        self.sio_drawer = sio_drawer
    def callback(self, message):
        try:
            sourceId = message.get("sourceId", "unknown")
            analyticsTimestamp = message.get("analyticsTimestamp",0)
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analyticsTimestamp/1000))
            print (f"Received message from source {sourceId} at {timestamp_str}")
            
            mediaEvents = message.get("mediaEvents", {})
            for event in mediaEvents:
                type = event.get("type", "unknown")
                msg = event.get("msg", "unknown")
                if type == "image":
                    file_path = f"/tmp/sio/{sourceId}_{os.path.basename(msg)}"
                    print(f"Downloading image {msg} from source {sourceId} to {file_path}")
                    self.sio_drawer.set_current_frame(self.mcp_client.get_image(sourceId, msg))
                    self.sio_drawer.save_frame(file_path)
                    # Draw SIO Data
                    file_path = f"/tmp/sio/output_{sourceId}_{os.path.basename(msg)}"
                    print(f"Drawing SIO data to {file_path}")
                    self.sio_drawer.draw_sio_data(message)
                    self.sio_drawer.save_frame(file_path)

        except Exception as e:
            print(f"Caught exception {e} handling callback")
            traceback.print_exc()
            