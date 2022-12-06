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

    def __init__(self,  capture_dir=None, sensors_json = None, annotated_subdir=None):
        self.capture_dir = capture_dir
        if self.capture_dir is None:
            self.capture_dir = MCPEventAnnotator.DEFAULT_CAPTURE_DIR
        self.annotated_subdir = annotated_subdir
        if self.annotated_subdir is None:
            self.annotated_subdir = MCPEventAnnotator.DEFAULT_ANNOTATED_VIDEO_WRITE_SUBDIR
        self.roi_filter = None
        if sensors_json:
            self.roi_filter = ROIFilter(sensors_json)

    def annotate_frame_with_event(self, frame, data):
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

    def create_annotation(self, jsonfile, vidfile, annotated_vid):
        event_segment = json.load(open(jsonfile))
        vid_capture = cv2.VideoCapture(str(vidfile))
        fps = vid_capture.get(cv2.CAP_PROP_FPS)
        frame_advance_ts = 1000/fps
        total_frames = (event_segment['end_ts'] - event_segment['start_ts']) / frame_advance_ts
        frame_count = 0
        frame_ts = event_segment['start_ts']
        event_list_index = 0
        frame_size = (int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        output = cv2.VideoWriter(str(annotated_vid),
                                cv2.VideoWriter_fourcc('M','P','4','V'),
                                vid_capture.get(cv2.CAP_PROP_FPS),
                                frame_size)

        while(vid_capture.isOpened()):
        # vid_capture.read() methods returns a tuple, first element is a bool
        # and the second is frame
            ret, frame = vid_capture.read()
            frame_count = frame_count + 1
            if ret == True:
                frame_ts_next = frame_ts + frame_advance_ts
                if event_list_index < len(event_segment['events_list']):
                    next_event = event_segment['events_list'][event_list_index]
                    if frame_ts <= next_event['frameTimestamp'] <= frame_ts_next:
                        self.annotate_frame_with_event(frame, next_event)
                        event_list_index = event_list_index + 1
                self.annotate_frame_with_sensors(frame)
                # Write the frame to the output files
                output.write(frame)
                print(f"Wrote frame {frame_count}")
                frame_ts = frame_ts_next
            else:
                print("Stream ended")
                break

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
    parser.add_argument("--capture_dir", help="Directory to store captured video (default is " + MCPEvents.DEFAULT_CAPTURE_DIR + ")")
    parser.add_argument("--sensors_json", help="sensors.json to use for RIO display")
    args = parser.parse_args()
    annotator = MCPEventAnnotator(args.capture_dir, args.sensors_json)
    annotator.main()


