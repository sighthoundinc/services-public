import signal
import sys
import argparse
from AMQPListener import AMQPListener
from EventSegment import EventSegment
from MCPFetcher import MCPFetcher
from ROIFilter import ROIFilter
import datetime
from pathlib import Path
import json

class MCPEvents:
    DEFAULT_CAPTURE_DIR="video_captures"
    def __init__(self, host,  mcp_username, mcp_password, capture_dir=None, sensors_json=None):
        self.listener = None
        self.fetcher = MCPFetcher(host, mcp_username, mcp_password)
        self.host = host
        # Location to write video captures
        if not capture_dir:
            capture_dir = MCPEvents.DEFAULT_CAPTURE_DIR

        self.path_prefix=Path(capture_dir)
        self.current_event_seg = {}
        # Group events into a single segment when separated
        # by less than this number of milliseconds
        self.group_events_separation_ms = 5*1000
        # Consider events ended when they reach this maximum length
        # in milliseconds
        self.group_events_max_length = 60*1000
        # The amount to extend the video capture duration before/after
        # the event segment, in ms
        self.event_capture_extend_duration_ms = 1000
        self.roi_filter = None
        if sensors_json:
            self.roi_filter = ROIFilter(sensors_json)

    def signal_handler(sig, frame):
        print('Exit due to ctrl->c')
        sys.exit(0)

    def video_callback(self, file_path, event_segment):
        print(f"Video written to {file_path} with {len(event_segment.events_list)} events")
        try:
            with open(str(file_path) + ".json", 'w') as f:
                json.dump(event_segment, f, indent=4, default=vars)
            print(f"Event json written to {file_path}.json")
        except Exception as e:
            print(f"Caught exception {e} dumping event segment to {file_path}.json")
            raise

    @staticmethod
    def frame_timestamp_to_timestr(frame_ts):
        ts = datetime.datetime.fromtimestamp(frame_ts//1000)
        return ts.strftime('%Y-%m-%d-%H-%M-%S')

    def new_event_segment(self, source, event_segment, max_ts):
        min_duration_seconds = 1
        time_str = self.frame_timestamp_to_timestr(event_segment.start_ts)
        duration_s = (event_segment.end_ts-event_segment.start_ts)//1000
        event_segment.start_ts = event_segment.start_ts - self.event_capture_extend_duration_ms
        event_segment.end_ts = event_segment.end_ts + self.event_capture_extend_duration_ms
        filename=f"{source}_{time_str}_{duration_s}s_{len(event_segment.events_list)}_events.mkv"
        print(f"New event segment detected, capturing video at {filename}")
        self.fetcher.fetch_video_async( source,
                                        self.path_prefix / filename,
                                        event_segment
                                        )

    def json_callback(self, data):
        if 'frameTimestamp' in data and 'sourceId' in data and \
                data['sourceId'] in self.current_event_seg:
            current_event_seg = self.current_event_seg[data['sourceId']]
            if data['frameTimestamp'] - current_event_seg.start_ts > \
                    self.group_events_max_length :
                print(f"Event length exceeded {self.group_events_max_length} ms, restarting event segment")
                self.new_event_segment(data['sourceId'],current_event_seg, data['frameTimestamp'])
                del self.current_event_seg[data['sourceId']]

            elif data['frameTimestamp'] - current_event_seg.end_ts > \
                    self.group_events_separation_ms :
                print(f"More than {self.group_events_separation_ms} ms between events, restarting event segment")
                print(f"Current frame timestamp is {self.frame_timestamp_to_timestr(data['frameTimestamp'])}"\
                        f" last event timestamp was {self.frame_timestamp_to_timestr(current_event_seg.end_ts)}")
                self.new_event_segment(data['sourceId'],current_event_seg, data['frameTimestamp'])
                del self.current_event_seg[data['sourceId']]
        if 'metaClasses' in data and 'sourceId' in data:
            if not self.roi_filter or self.roi_filter.objects_in_roi(data):
                if not data['sourceId'] in self.current_event_seg:
                    self.current_event_seg[data['sourceId']] = EventSegment(data['frameTimestamp'])
                current_event_seg = self.current_event_seg[data['sourceId']]
                current_event_seg.events_list.append(data)
                current_event_seg.end_ts = data['frameTimestamp']
                #print(f"Handled event {data}")

    def start(self):
        self.path_prefix.mkdir(parents=True, exist_ok=True)
        self.fetcher.start(self.video_callback)
        self.listener = AMQPListener(self.host)
        print(f"Starting AMQP listener for {self.host}")
        self.listener.start(self.json_callback)


    def stop(self):
        self.listener.stop()

    def main(self):
        self.start()
        print(f"Listening on {self.host}")
        signal.signal(signal.SIGINT, self.signal_handler)
        while True:
            signal.pause()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Host name or IP")
    parser.add_argument("--capture_dir", help="Directory to store captured video (default is " + MCPEvents.DEFAULT_CAPTURE_DIR + ")")
    parser.add_argument("--sensors_json", help="sensors.json to use for RIO filtering")
    parser.add_argument("--mcp_username", help="Username for MCP", default="root")
    parser.add_argument("--mcp_password", help="Password for MCP", default="root")
    args = parser.parse_args()
    events = MCPEvents(args.host, args.mcp_username, args.mcp_password, args.capture_dir, args.sensors_json)
    events.main()


