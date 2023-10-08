import json
import traceback
import sys
from shapely import geometry

def convert_box_to_polygon(box):
  return geometry.Polygon(
      [
          [box["x"], box["y"]],
          [box["x"] + box["width"], box["y"]],
          [box["x"] + box["width"], box["y"] + box["height"]],
          [box["x"], box["y"] + box["height"]],
      ]
  )
class SIOPlugin:
  def __init__(self):
    self.outputFile = None

  # Prepare the module
  def configure(self, configJsonPath):
    print("#######################")
    pass

  # Process the output
  def process(self, tick, frameData, frame):
    if frameData is not None and frameData != '':
      try:
        data = json.loads(frameData)
        if "metaClasses" in data:
          objects = {}
          for metaClass in data["metaClasses"]:
            for objId in data["metaClasses"][metaClass]:
              objects[objId] = data["metaClasses"][metaClass][objId]
              objects[objId]["poly"] = convert_box_to_polygon(objects[objId]["box"])
          # Calculate the distance between the objects
          if len(objects) > 1:
            newFrameData = json.loads(frameData)
            newFrameData["distances"] = {}
            for objId in objects:
              for objId2 in objects:
                if objId != objId2:
                  newFrameData["distances"][objId] = {"object": objId2, "distance" : objects[objId]["poly"].distance(objects[objId2]["poly"])}
            return json.dumps(newFrameData)
      except:
        print(f"{type(self).__name__} Failed:", file=sys.stderr)
        print("%s" % traceback.format_exc(), file=sys.stderr, flush=True)
        return frameData
    return frameData

  # Finalize the module
  def finalize(self):
    pass