import traceback

class SIODrawerCallback:
    def __init__(self, sio_factory, mcp):
        self.sio_factory = sio_factory
        self.mcp = mcp
        self.last_sequence = 0

    def callback(self, data):
        try:
            if "frameDimensions" in data:
                self.sio_factory.set_frame_size(data["frameDimensions"]["w"], data["frameDimensions"]["h"])
            

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
                try:
                    self.sio_factory.set_current_frame(self.mcp.get_image(source_id, image_found))
                except Exception as e:
                    print(f"Caught exception {e}")
            else:
                return
               

            self.sio_factory.write_text(str(data.get("frameTimestamp", 0)), "top_left")
            
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
                    self.sio_factory.draw_rectangle(x, y, w, h, title=object_id, color=green)

        except Exception as e:
            print(f"Caught exception {e} handling sio callback")
            traceback.print_exc()
        else:
            self.sio_factory.update_frame()