import traceback
import time

class SIO:
    def __init__(self) -> None:
        pass
    def callback(self, message):
        try:
            sourceId = message.get("sourceId", "unknown")
            frameId = message.get("frameId", "unknown")
            analyticsTimestamp = message.get("analyticsTimestamp",0)
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analyticsTimestamp/1000))
            output = f"Message from source: {sourceId} frame: {frameId} at {timestamp_str}\n"
            
            metaclasses = message.get("metaClasses", {})
            if metaclasses:
                output += " With objects:\n"
            for metaclass, objects in metaclasses.items():
                for object_id, object in objects.items():
                    object_class = object.get("class", "unknown")
                    box = object.get("box", {})
                    x = box.get("x", -1)
                    y = box.get("y", -1)
                    output += f"  - {metaclass}:{object_class} ({object_id})  at ({x},{y})\n"

            mediaEvents = message.get("mediaEvents", {})
            if mediaEvents:
                output += " With media events:\n"
            for event in mediaEvents:
                    type = event.get("type", "unknown")
                    sequence = event.get("sequence", -1)
                    output += f"  - {type} ({sequence})\n"

            output += "---------------\n"
            print(output)
            
            
        except Exception as e:
            print(f"Caught exception {e} handling callback")
            traceback.print_exc()
            