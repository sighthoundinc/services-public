import dataclasses
from pathlib import Path
import os
import cv2
import json
from EventSegment import EventSegment
from MCPEvents import MCPEvents
from ROIFilter import ROIFilter
import argparse
import numpy as np

class MCPEventAnnotator:
    DEFAULT_CAPTURE_DIR="video_captures"
    DEFAULT_ANNOTATED_VIDEO_WRITE_SUBDIR="annotated"
    DEFAULT_DISPLAY_TIMESTAMPS = False

    def __init__(self,  capture_dir=None, sensors_json = None, annotated_subdir=None, timestamp_display=False):
        self.capture_dir = capture_dir
        if self.capture_dir is None:
            self.capture_dir = MCPEventAnnotator.DEFAULT_CAPTURE_DIR
        self.annotated_subdir = annotated_subdir
        if self.annotated_subdir is None:
            self.annotated_subdir = MCPEventAnnotator.DEFAULT_ANNOTATED_VIDEO_WRITE_SUBDIR
        self.roi_filter = None
        if sensors_json:
            self.roi_filter = ROIFilter(sensors_json)
        self.timestamp_display = timestamp_display

    def annotate_frame_with_event(self, frame, data):
        annotated = False
        metaclasses = data['metaClasses']
        frame_dimensions = data['frameDimensions']
        region_map = None
        if self.roi_filter:
            region_map = self.roi_filter.get_object_region_map(data)

        for metaclass in metaclasses.keys():
            for obj_id in metaclasses[metaclass].keys():
                obj_dict = metaclasses[metaclass][obj_id]
                if 'box' in obj_dict:
                    x_norm = obj_dict['box']['x']/frame_dimensions['w']
                    y_norm = obj_dict['box']['y']/frame_dimensions['h']
                    w_norm = obj_dict['box']['width']/frame_dimensions['w']
                    h_norm = obj_dict['box']['height']/frame_dimensions['h']
                    height = frame.shape[0]
                    width = frame.shape[1]
                    x = x_norm * width
                    y = y_norm * height
                    w = w_norm * width
                    h = h_norm * height
                    color = (0, 0, 255)
                    if region_map and obj_id in region_map:
                        color = (0, 255, 0)
                    cv2.rectangle(frame, (int(x+w), int(y+h)), (int(x),int(y)), color, 2)
                    cv2.putText(frame, obj_dict['class'], (int(x),int(y+8)), cv2.FONT_HERSHEY_SIMPLEX,
                                    1, color, 2, cv2.LINE_AA)
                    annotated = True
        return annotated

    def annotate_frame_with_timestamp(self, frame, anypipe_timestamp, video_timestamp):
        
        if video_timestamp:
            cv2.putText(frame, str(video_timestamp), (40,70), cv2.FONT_HERSHEY_SIMPLEX,
                        1.15 , (255, 255, 0), 2, cv2.LINE_AA, False)
        if anypipe_timestamp:
            cv2.putText(frame, str(anypipe_timestamp), (40,110), cv2.FONT_HERSHEY_SIMPLEX,
                        1.15 , (255, 255, 0), 2, cv2.LINE_AA, False)

    def annotate_frame_with_sensors(self, frame):
        poly_points = {}
        if self.roi_filter:
            for region in self.roi_filter.regions:
                xx, yy = region.polygon.exterior.coords.xy
                height = frame.shape[0]
                width = frame.shape[1]
                xx_scaled = [ int(x * width) for x in xx ]
                yy_scaled = [ int(y * height) for y in yy ]
                poly_points[region.name] =np.array(list(zip(xx_scaled, yy_scaled)))
            for name in poly_points.keys():
                cv2.polylines(frame, [poly_points[name]], True, (255,0,0), 2)

    def get_overall_fps(self, vidfile):
        vid_capture = cv2.VideoCapture(str(vidfile))
        fps = vid_capture.get(cv2.CAP_PROP_FPS)
        if fps > 60 or fps < 0:
            print(f"Found bogus fps {fps}, calculating")
            reported_fps = fps
            last_frame = 0
            last_time = 0
            # See https://stackoverflow.com/a/52463543
            while vid_capture.isOpened():
                ret, frame = vid_capture.read()
                if ret:
                    time = vid_capture.get(cv2.CAP_PROP_POS_MSEC)
                    if time > last_time:
                        last_time = time
                    elif last_frame > 0:
                        print(f"Got bogus time {time} on frame {last_frame}")
                    last_frame = last_frame +1
                else:
                    break
            if last_frame == 0:
                fps = 0
            else:
                fps = last_frame / (last_time/1000)
            print(f"Found bogus FPS {reported_fps} in video, calculated overall fps {fps}")

        return fps

    def create_annotation(self, jsonfile, vidfile, annotated_vid):
        event_segment = json.load(open(jsonfile))
        frame_count = 0
        event_list_index = 0
        annotated_frame_count = 0
        overall_fps = self.get_overall_fps(vidfile)
        vid_capture = cv2.VideoCapture(str(vidfile))
        frame_size = (int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        output = cv2.VideoWriter(str(annotated_vid),
                                cv2.VideoWriter_fourcc('m','p','4','v'),
                                overall_fps,
                                frame_size)
        ret, frame = vid_capture.read()
        while(vid_capture.isOpened()):
        # vid_capture.read() methods returns a tuple, first element is a bool
        # and the second is frame
            video_ts_ms = vid_capture.get(cv2.CAP_PROP_POS_MSEC)
            next_ret, next_frame = vid_capture.read()
            video_ts_next = vid_capture.get(cv2.CAP_PROP_POS_MSEC)
            frame_count = frame_count + 1
            frame_ts = event_segment['start_ts'] + video_ts_ms
            frame_ts_next = event_segment['start_ts'] + video_ts_next
            annotated_frame = False
            anypipe_frame_ts = 0
            if ret == True:
                if event_list_index < len(event_segment['events_list']):
                    next_event = event_segment['events_list'][event_list_index]
                    while frame_ts <= next_event['frameTimestamp'] <= frame_ts_next:
                        if self.annotate_frame_with_event(frame, next_event):
                            print(f"Wrote frame {frame_count} and annotated with event at timestamp {next_event['frameTimestamp']}")
                            annotated_frame_count = annotated_frame_count +1
                            annotated_frame = True
                            anypipe_frame_ts = next_event['frameTimestamp']
                        event_list_index = event_list_index + 1
                        if event_list_index < len(event_segment['events_list']):
                            next_event = event_segment['events_list'][event_list_index]
                        else:
                            break


                self.annotate_frame_with_sensors(frame)
                if self.timestamp_display:
                    self.annotate_frame_with_timestamp(frame, anypipe_frame_ts, frame_ts)
                # Write the frame to the output files
                output.write(frame)
                if not annotated_frame:
                    print(f"Wrote frame {frame_count} without event annotation")
                frame = next_frame
                ret = next_ret
            else:
                print("Stream ended")
                break

        print(f"Processed {len(event_segment['events_list'])} events, annotated {annotated_frame_count} frames")
        vid_capture.release()
        output.release()

    def main(self):
        files = Path(self.capture_dir).glob('*.json')
        annotated_subdir = Path(self.capture_dir) / Path(self.annotated_subdir)
        annotated_subdir.mkdir(parents=True, exist_ok=True)
        self.annotated_subdir
        for jsonfile in files:
            vidfile = Path(self.capture_dir) / jsonfile.stem
            if os.path.isfile(vidfile):
                self.create_annotation(jsonfile, vidfile, annotated_subdir/jsonfile.stem)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture_dir", help="Directory to store captured video (default is " + MCPEvents.DEFAULT_CAPTURE_DIR + ")", default=MCPEvents.DEFAULT_CAPTURE_DIR)
    parser.add_argument("--sensors_json", help="sensors.json to use for RIO display")
    parser.add_argument("--timestamps", help="Whether to display timestamps on the video (default is " + str(MCPEventAnnotator.DEFAULT_DISPLAY_TIMESTAMPS) + ")", default=MCPEventAnnotator.DEFAULT_DISPLAY_TIMESTAMPS)
    args = parser.parse_args()
    annotator = MCPEventAnnotator(args.capture_dir, args.sensors_json, timestamp_display=args.timestamps)
    annotator.main()


