import dataclasses
from pathlib import Path
import os
import cv2
import json
from EventSegment import EventSegment
from ROIFilter import ROIFilter
import argparse
import numpy as np
import m3u8

class MCPEventAnnotator:
    DEFAULT_CAPTURE_DIR="video_captures"
    DEFAULT_ANNOTATED_VIDEO_WRITE_SUBDIR="annotated"
    DEFAULT_DISPLAY_TIMESTAMPS = False
    DEFAULT_POSTPROCESS_SENSORS = False

    def __init__(self,
                    capture_dir=None,
                        sensors_json = None,
                        annotated_subdir=None,
                        timestamp_display=DEFAULT_DISPLAY_TIMESTAMPS,
                        postprocess_sensors=DEFAULT_POSTPROCESS_SENSORS):
        self.capture_dir = capture_dir
        if self.capture_dir is None:
            self.capture_dir = MCPEventAnnotator.DEFAULT_CAPTURE_DIR
        self.annotated_subdir = annotated_subdir
        if self.annotated_subdir is None:
            self.annotated_subdir = MCPEventAnnotator.DEFAULT_ANNOTATED_VIDEO_WRITE_SUBDIR
        self.roi_filter = None
        self.sensor_annotations = {}
        if sensors_json:
            self.roi_filter = ROIFilter(sensors_json)
            self.init_sensors()
        self.timestamp_display = timestamp_display

        self.postprocess_sensors = postprocess_sensors

    def get_sensor_name(self, sensor_id):
        region_name = "unknown"
        if self.roi_filter:
            region = self.roi_filter.get_roi_region(sensor_id)
            if region is not None:
                region_name = region.name
        return region_name

    def init_sensor_id(self, sensor_id, text = "unknown"):
        if sensor_id not in self.sensor_annotations:
            self.sensor_annotations[sensor_id] = {}
        self.sensor_annotations[sensor_id]['objects'] = {}
        self.sensor_annotations[sensor_id]['text']  = f"{self.get_sensor_name(sensor_id)}: {text}"
        self.sensor_annotations[sensor_id]['text_color'] = (255, 0, 0)
        self.sensor_annotations[sensor_id]['objects_in_region'] = 0

    def init_sensors(self):
        for region in self.roi_filter.get_regions():
            self.init_sensor_id(region.id)


    def analyze_sensor_events(self, data):
        if 'sensorEvents' in data:
            if 'presenceSensor' in data['sensorEvents']:
                for sensorId in data['sensorEvents']['presenceSensor']:
                    presence_events = data['sensorEvents']['presenceSensor'][sensorId]
                    for presence_event in presence_events:
                        sensor_object_info = {}
                        if 'links' in presence_event:
                            for link in presence_event['links']:
                                if link['id'] not in sensor_object_info:
                                    sensor_object_info[link['id']] = {}
                                frame_object = sensor_object_info[link['id']]
                                if 'state' in link:
                                    if link['state'] == 'enter':
                                        frame_object['color'] = (0, 255, 0)
                                    if link['state'] == 'present':
                                        frame_object['color'] = (0, 255, 255)
                                    if link['state'] == 'exit':
                                        frame_object['color'] = (255, 0, 0)

                        if sensorId not in self.sensor_annotations:
                            self.sensor_annotations[sensorId] = {}
                        objects_count = presence_event['objectsInRegionCount']
                        if objects_count:
                            sensor_text = f"{self.get_sensor_name(sensorId)}: {objects_count} filtered objects in region"
                            if 'people' in presence_event['objectsCountbyMetaClass']:
                                sensor_text += f", {presence_event['objectsCountbyMetaClass']['people']} people"
                            if 'vehicles' in presence_event['objectsCountbyMetaClass']:
                                sensor_text += f", {presence_event['objectsCountbyMetaClass']['vehicles']} vehicles"
                            self.sensor_annotations[sensorId]['text'] = sensor_text
                            self.sensor_annotations[sensorId]['text_color'] = (0, 255, 0)
                        else:
                            self.init_sensor_id(sensorId, text = "no configured objects")
                        self.sensor_annotations[sensorId]['objects'] = sensor_object_info
                        self.sensor_annotations[sensorId]['objects_in_region'] = objects_count


    def annotate_sensor_events(self, frame):
        annotated = False
        text_offset = 150
        for sensor_id in self.sensor_annotations:
            annotated = True
            cv2.putText(frame, self.sensor_annotations[sensor_id].get('text',''), (40,text_offset), cv2.FONT_HERSHEY_SIMPLEX,
                1.15 , self.sensor_annotations[sensor_id]['text_color'], 2, cv2.LINE_AA, False)
            text_offset += 40
        return annotated


    def get_sensor_object_color(self, object_id, data):
        color = (0, 0, 255)
        if self.postprocess_sensors:
            region_map = None
            if self.roi_filter:
                region_map = self.roi_filter.get_object_region_map(data)
                if object_id in region_map:
                    color = (0, 255, 0)
        for sensor_id in self.sensor_annotations:
            if 'objects' in self.sensor_annotations[sensor_id] and \
                object_id in self.sensor_annotations[sensor_id]['objects'] and\
                    'color' in self.sensor_annotations[sensor_id]['objects'][object_id]:
                    color = self.sensor_annotations[sensor_id]['objects'][object_id]["color"]
        return color

    def annotate_frame_with_event(self, frame, data):
        annotated = False
        metaclasses = data['metaClasses']
        frame_dimensions = data['frameDimensions']

        self.analyze_sensor_events(data)

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
                    color = self.get_sensor_object_color(obj_id, data)
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
            for region_id in self.roi_filter.regions:
                region = self.roi_filter.regions[region_id]
                xx, yy = region.polygon.exterior.coords.xy
                height = frame.shape[0]
                width = frame.shape[1]
                xx_scaled = [ int(x * width) for x in xx ]
                yy_scaled = [ int(y * height) for y in yy ]
                poly_points[region.name] = {
                    "array" : np.array(list(zip(xx_scaled, yy_scaled))),
                    "color" : (0, 255, 0) if self.sensor_annotations[region_id]['objects_in_region'] else (255, 0, 0)
                }
            for name in poly_points.keys():
                cv2.polylines(frame, [poly_points[name]['array']], True,
                                     poly_points[name]['color'], 2)

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
        vid_capture.release()
        return fps

    def get_vidfiles(self, vidfile, event_segment):
        vidfiles = [vidfile]
        start_timestamps = [event_segment['start_ts']]
        if vidfile.suffix == ".m3u8":
            vidfiles = []
            start_timestamps = []
            playlist = m3u8.load(str(vidfile))
            for segment in playlist.segments:
                file = segment.uri
                if Path(file).is_absolute():
                    vidfiles.append(Path(file))
                else:
                    vidfiles.append(vidfile.parent / Path(file))
                has_timestamp = False
                for video in event_segment['videos']:
                    if video['msg'] in segment.uri:
                        start_timestamps.append(video['startTs'])
                        has_timestamp = True
                        break
                if not has_timestamp:
                    start_timestamps.append(None)

        return vidfiles, start_timestamps

    def create_annotation(self, jsonfile, vidfile):
        annotated_subdir = Path(vidfile).parent / Path(self.annotated_subdir)
        annotated_subdir.mkdir(parents=True, exist_ok=True)
        annotated_vid = Path(annotated_subdir)/Path(jsonfile).stem
        print(f"Creating video at {annotated_vid} for video at {vidfile} with json content at {jsonfile}")
        event_segment = json.load(open(jsonfile))
        frame_count = 0
        event_list_index = 0
        annotated_frame_count = 0
        vidfiles, start_timestamps = self.get_vidfiles(vidfile, event_segment)
        overall_fps = self.get_overall_fps(vidfiles[0])
        vid_capture = cv2.VideoCapture(str(vidfiles[0]))
        frame_size = (int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        output = cv2.VideoWriter(str(annotated_vid) + ".mp4",
                                cv2.VideoWriter_fourcc('m','p','4','v'),
                                overall_fps,
                                frame_size)

        for vidfile, start_ts in zip(vidfiles, start_timestamps):
            if start_ts is None:
                print(f"Skipping video {vidfile} since no start timestamp was captured for this file")
                continue
            vid_capture.release()
            vid_capture = cv2.VideoCapture(str(vidfile))
            ret, frame = vid_capture.read()
            stream_ended = False
            while(vid_capture.isOpened() and not stream_ended):
                video_ts_ms = vid_capture.get(cv2.CAP_PROP_POS_MSEC)
                # vid_capture.read() methods returns a tuple, first element is a bool
                # and the second is frame
                next_ret, next_frame = vid_capture.read()
                video_ts_next = vid_capture.get(cv2.CAP_PROP_POS_MSEC)
                frame_count = frame_count + 1
                frame_ts = start_ts + video_ts_ms
                frame_ts_next = start_ts + video_ts_next
                annotated_frame = False
                anypipe_frame_ts = 0
                if ret == True:
                    self.frame_info = {}
                    if event_list_index < len(event_segment['events_list']):
                        next_event = event_segment['events_list'][event_list_index]
                        while frame_ts <= next_event['frameTimestamp'] <= frame_ts_next:
                            if self.annotate_frame_with_event(frame, next_event):
                                annotated_frame_count = annotated_frame_count +1
                                annotated_frame = True
                                anypipe_frame_ts = next_event['frameTimestamp']
                            event_list_index = event_list_index + 1
                            if event_list_index < len(event_segment['events_list']):
                                next_event = event_segment['events_list'][event_list_index]
                            else:
                                break

                    if self.annotate_sensor_events(frame):
                        annotated_frame = True
                    self.annotate_frame_with_sensors(frame)
                    if self.timestamp_display:
                        self.annotate_frame_with_timestamp(frame, anypipe_frame_ts, frame_ts)
                    # Write the frame to the output files
                    output.write(frame)
                    frame = next_frame
                    ret = next_ret
                else:
                    print("Stream ended")
                    stream_ended = True
            print(f"Video at {annotated_vid} complete, processed {len(event_segment['events_list'])} events, annotated {annotated_frame_count} frames")
        output.release()

    def main(self):
        files = list(Path(self.capture_dir).glob('*.json'))
        files.extend(list(Path(Path(self.capture_dir) / Path('json')).glob('*.json')))
        annotated_subdir = Path(self.capture_dir) / Path(self.annotated_subdir)
        annotated_subdir.mkdir(parents=True, exist_ok=True)
        has_json_file = False

        for jsonfile in files:
            has_json_file = True
            vidfile = Path(self.capture_dir) / jsonfile.stem
            if not os.path.isfile(vidfile):
                vidfile = None
                capture_dir_matches = list(Path(self.capture_dir).glob(f"{jsonfile.stem}.*"))
                if len(capture_dir_matches) == 1:
                    vidfile = capture_dir_matches[0]
            if vidfile:
                self.create_annotation(jsonfile, vidfile)
            else:
                print(f"Could not find video to match {jsonfile}, no annotation performed")
        if not has_json_file:
            print(f"No json files found at {self.capture_dir}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture_dir", help="Directory to store captured video (default is " + MCPEventAnnotator.DEFAULT_CAPTURE_DIR + ")", default=MCPEventAnnotator.DEFAULT_CAPTURE_DIR)
    parser.add_argument("--sensors_json", help="sensors.json to use for RIO display")
    parser.add_argument("--timestamps", help="Whether to display timestamps on the video (default is " + str(MCPEventAnnotator.DEFAULT_DISPLAY_TIMESTAMPS) + ")", default=MCPEventAnnotator.DEFAULT_DISPLAY_TIMESTAMPS)
    parser.add_argument("--postprocess_sensors", help="Whether to post process sensors or only use sensor data in event (default is " + str(MCPEventAnnotator.DEFAULT_POSTPROCESS_SENSORS) + ")", default=MCPEventAnnotator.DEFAULT_POSTPROCESS_SENSORS)
    args = parser.parse_args()
    annotator = MCPEventAnnotator(args.capture_dir,
                                    args.sensors_json,
                                    timestamp_display=args.timestamps,
                                    postprocess_sensors = args.postprocess_sensors)
    annotator.main()


