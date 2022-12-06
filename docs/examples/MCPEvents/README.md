# Overview

The scripts in this directory capture video clips corresponding to events segments detected by SIO and processed by MCP.

Clips are captured based on requests to the MCP component based on time regions of interest
corresponding to SIO event segments, where event segments correspond to sequences of video where SIO events are detected.

For now, hack on the MCPEvents.py file to configure/control captures and definition of event sequences. See the comments in `MCPEvents.py` and detail below for tuning parameters.

These scripts all assume they are running on a host with routable IP access to the device/system running MCP.
If MCP is running on a camera/node it's currently assumed the scripts are hosted from an x86 host on the same network.

## Setup

Install python requirements with:
```
pip3 install -r requirements.txt
```

Install these dependencies on Ubuntu platforms
```
sudo apt-get install -y ffmpeg  libx264-dev
```

## Overview

The scripts are used in two phases:
1) Event Capture which records videos and JSON dumps based on interesting regions of
time and associated video.
2) Event Annotation which takes the video and JSON dumps from the previous steps and
overlays bounding boxes, creates annotated video segments to visualize the data
output from the pipeline.

### Event Capture

The command

```
python3 MCPEvents.py 10.1.10.154
```

Will capture events using the instance at 10.1.10.154 and write videos associated with events as
well as a json file containing all events captured during the video duration to a
`video_captures` subdirectory.  This implementation captures events based on
all events recieved from SIO.  Events are captured when more than group_events_separation_ms occurs
between events OR when up to group_events_max_length of time expires without a separation gap.
These two values are currently set to 5 seconds and 60 seconds respectively and can be tuned for the application in
MCPEvents.py

#### Filtering based on ROI

The command
```
python3 MCPEvents.py --sensor_json sensors.json 10.1.10.154
```
Will filter all captures based on regions defined in sensors.json, where the
sensors.json file can be built and exported at http://public-sh-sensor-config-dev.s3-website-us-east-1.amazonaws.com/
using an image captured from an export of one of the images of the videos captured in the step above.

Objects are considered to be in the region of interest if the bottom right corner
of the bounding box is in the region.  This is not (yet) configurable but can be customized
in the ROIFilter class.

### Event Annotation

The command:
```
python3 MCPEventAnnotator.py
```

Will annotate the videos captured in the previous `MCPEvents` capture step, based on the event logs associated with captured videos

The command:
```
python3 MCPEventAnnotator.py --sensor_json sensors.json
```

Will include an overlay of the sensors in sensors.json on the annotated videos when
annotating.

## Limitations and Future Work

1) The tool only supports region of interest sensors.  Line sensors are not supported.
2) Most tuning parameters are hard coded and not accepted as arguments.
3) MCP authentication parameters are hardcoded in MCPFetcher.py and are assumed to be defaults.
4) Events aren't perfectly synchronized in the event annotator, and differences between
video and annotations of ~1 second are currently likely to occur.
