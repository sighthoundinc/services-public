#
# Sample SIO pipeline extension
#

import sys
import os
import json

class SIOPlugin:
  def __init__(self):
    print(f"Creating SIO extension")
    self.prefix = "unknown"

  # Prepare the module using provided configuration
  def configure(self, configJsonPath):
    try:
      with open(configJsonPath) as configJsonFile:
          config = json.load(configJsonFile)
      self.prefix = config["prefix"]
    except:
      print(f"Failed to load extension module configuration from {configJsonPath}")
      raise

  # Process the output
  def process(self, tick, frameData, frame):
    # This extension doesn't do much, just logging the analytics. However, you could
    # implement an egress method alternative to AMQP, additional filtering of the results,
    # modifying the resulting JSON, annotating the images etc.
    # Just remember not to block -- or not to spend too much time -- here.
    print(f"{self.prefix} - {tick} - {frameData}")

    # always return the (potentially filtered or modified) output
    return frameData

  # Finalize the module
  def finalize(self):
    print(f"{self.prefix} - Pipeline completed")
