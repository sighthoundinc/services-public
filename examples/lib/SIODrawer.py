import traceback
import cv2
import numpy as np

class SIODrawer:
    def __init__(self, mcp=None, stream_factory=None):
        self.stream_factory = stream_factory
        self.mcp = mcp
        self.last_sequence = 0
        self.frame = None

    def set_current_frame(self, frame):
        self.frame = frame

    def clear_frame(self, color=None):
        if color is not None:
            self.frame = np.full((self.height, self.width, self.channels), color, np.uint8)
        else:
            self.frame = np.zeros((self.height, self.width, self.channels), np.uint8)
            self.write_text("No frame", location="center", color=(0, 0, 255), font_scale=2, thickness=3)

    def save_frame(self, filename):
        cv2.imwrite(filename, self.frame)

    def draw_a_circle(self):
        # Calculate the center point of the image
        center = (int(self.width/2), int(self.height/2))
        # Draw a circle at the center point
        radius = 50
        color = (0, 0, 255) # BGR format
        thickness = 2
        cv2.circle(self.frame, center, radius, color, thickness)

    def draw_rectangle(self, x, y, w, h, title=None, color = (0, 255, 0)):
        # Draw a rectangle
        cv2.rectangle(self.frame, (x, y), (x+w, y+h), color, 2)
        # Draw a title
        if title != None:
            cv2.putText(self.frame, title, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def write_text(self, text, location="top_left", color=(0, 255, 0), font_scale=1, thickness=2):
        if location == "bottom_left":
            x = 10
            y = self.height - 10
        elif location == "top_left":
            x = 10
            y = 30
        elif location == "center":
            str_len = len(text)
            x = int(self.width / 2) - (str_len * font_scale * 10 )
            y = int(self.height / 2)
        else:
            print("Invalid location. Using top_left")
            x = 10
            y = 30
        cv2.putText(self.frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    def draw_sio_data(self, data):
        self.write_text(str(data.get("frameTimestamp", 0)), "top_left")
            
        # Draw objects
        # 'vehicles': {'my-video-car-386-1677705751799': {'class': 'car', 'firstFrameTimestamp': 1677706299912, 'bestDetectionTimestamp': 1677706299912, 'box': {'x': 1136, 'y': 315, 'width': 141, 'height': 129}, 'detectionScore': 0.77, 'updated': True}}
        for _metaClass, _classes in data.get("metaClasses", {}).items():
            # 'my-video-car-386-1677705751799': {'class': 'car', 'firstFrameTimestamp': 1677706299912, 'bestDetectionTimestamp': 1677706299912, 'box': {'x': 1136, 'y': 315, 'width': 141, 'height': 129}, 'detectionScore': 0.77, 'updated': True}
            for object_id, _object in _classes.items():
                # 'box': {'x': 1136, 'y': 315, 'width': 141, 'height': 129}
                box = _object.get("box", {})
                x = box.get("x", 0)
                y = box.get("y", 0)
                w = box.get("width", 0)
                h = box.get("height", 0)
                green = (0, 255, 0)
                self.draw_rectangle(x, y, w, h, title=object_id, color=green)

    def draw_sio_data_to_video(self, data, source, dest):
        # Get the time
        last_message = data[-1]
        startTs = 0
        endTs = 0
        for events in last_message.get("mediaEvents", 0):
            if events.get("type") == "video_file_closed":
                startTs = events.get("startTs", 0)
                endTs = events.get("endTs", 0)

        # Open the video file
        cap = cv2.VideoCapture(source)
        # Get the video width and height
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the output video file
        out = cv2.VideoWriter(dest+".mp4", cv2.VideoWriter_fourcc(*'mp4v'), 30, (self.width, self.height))
        while cap.isOpened():
            # Read a frame from the video
            ret, self.frame = cap.read()

            if ret:
                # Get the current position in milliseconds
                pos_msec = startTs + cap.get(cv2.CAP_PROP_POS_MSEC)
                
                # self.write_text(str(pos_msec), "bottom_left")

                # Draw objects
                message_found = False
                for message in data:
                    # Frame timestamp between now and 200ms after the current frame
                    if message.get("frameTimestamp", 0) >= pos_msec and message.get("frameTimestamp", 0) < pos_msec + 200:
                        message_found = True
                        self.draw_sio_data(message)
                        break
                if not message_found:
                    self.write_text("No message found", "center")


                # Write the frame to the output video file
                out.write(self.frame)
            else:
                break

        # Release the video capture and writer objects
        cap.release()
        out.release()

    def stream_callback(self, data):
        try:
            if "frameDimensions" in data:
                self.stream_factory.set_frame_size(data["frameDimensions"]["w"], data["frameDimensions"]["h"])
            
            # Draw image
            image_found = None
            source_id = data.get("sourceId", None)
            # [{'type': 'image', 'msg': '16777/1677706254368.jpg', 'format': 'jpg', 'sequence': 360}]
            for event in data.get("mediaEvents", []):
                if event.get("type") == "image":
                    if event.get("sequence") <= self.last_sequence:
                        continue
                    image_found = event.get("msg")
                    self.last_sequence = event.get("sequence")
                    break
            if image_found:
                print(f"- Received SIO data with images")
                try:
                    self.set_current_frame(self.mcp.get_image(source_id, image_found))
                except Exception as e:
                    print(f"Caught exception {e}")
            else:
                print(f"- Received SIO data without images")
                return
            
            self.draw_sio_data(data)
            
            self.stream_factory.set_current_frame(self.frame)

        except Exception as e:
            print(f"Caught exception {e} handling sio callback")
            traceback.print_exc()
        else:
            self.stream_factory.update_frame()