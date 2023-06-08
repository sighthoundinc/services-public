import signal
import sys
import argparse
import os
from lib.AMQPListener import AMQPListener
from lib.MCP import MCPClient
from EventSegment import EventSegment
from ROIFilter import ROIFilter
from MCPEventAnnotator import MCPEventAnnotator
import datetime
from pathlib import Path
import m3u8

class MCPEvents:
    def get_args(self, args):
        amqp_conf, mcp_conf = {}, {}
        amqp_conf["host"] = os.environ.get("AMQP_HOST", args.host)
        amqp_conf["port"] = os.environ.get("AMQP_PORT", 5672)
        amqp_conf["exchange"] = os.environ.get("AMQP_EXCHANGE", "anypipe")
        amqp_conf["routing_key"] = os.environ.get("AMQP_ROUTING_KEY", "#")
        print ("AMQP configuration:", amqp_conf)
        mcp_conf["host"] = os.environ.get("MCP_HOST", args.host)
        mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
        mcp_conf["username"] = os.environ.get("MCP_USERNAME", args.mcp_username)
        mcp_conf["password"] = os.environ.get("MCP_PASSWORD", args.mcp_password)
        print ("MCP configuration:", mcp_conf)
        return amqp_conf, mcp_conf

    def __init__(self, args):
        self.listener = None
        self.amqp_conf, mcp_conf = self.get_args(args)

        self.mcp_client = MCPClient(mcp_conf)
        self.host = args.host
        capture_dir = args.capture_dir
        # Location to write video captures
        if not capture_dir:
            capture_dir = MCPEventAnnotator.DEFAULT_CAPTURE_DIR

        self.path_prefix=Path(capture_dir)
        # The current event segment dict organized by sourceId, waiting for events to complete
        self.current_event_seg = {}
        # A dict of lists of completed event segments by sourceId, waiting to be written to disk when video is available
        self.completed_event_seg = {}
        # Group events into a single segment when separated
        # by less than this number of milliseconds. Only valid when use_events is not specified.
        self.group_events_separation_ms = 5*1000
        # Consider events ended when they reach this maximum length
        # in milliseconds. Only used when use_events is not specified.
        self.group_events_max_length = 60*1000
        self.roi_filter = None
        self.use_events = False
        if args.use_events:
            print("Generating events based on event generator output")
            self.use_events = True
            if args.sensors_json:
                print("Ignoring sensors.json argument for event capture since use_events is specified")
        else:
            if args.sensors_json:
                print("Generating events based on sensors.json")
                self.roi_filter = ROIFilter(args.sensors_json)
        if args.annotate:
            self.annotator = MCPEventAnnotator(capture_dir = capture_dir,
                                               sensors_json = args.sensors_json)

    def signal_handler(self, sig, frame):
        print('Exit due to ctrl->c')
        sys.exit(0)

    @staticmethod
    def frame_timestamp_to_timestr(frame_ts):
        ts = datetime.datetime.fromtimestamp(frame_ts//1000)
        return ts.strftime('%Y-%m-%d-%H-%M-%S')
    @staticmethod
    def frame_timestamp_to_dirstr(frame_ts):
        ts = datetime.datetime.fromtimestamp(frame_ts//1000)
        return ts.strftime('%Y-%m-%d')

    def new_event_segment(self, source, event_segment):
        if source not in self.completed_event_seg:
            self.completed_event_seg[source] = []
        self.completed_event_seg[source].append(event_segment)
        print("Event segment completed, waiting for video close")

    def event_segment_complete(self, source, event_segment):
        time_str = self.frame_timestamp_to_timestr(event_segment.start_ts)
        duration_s = (event_segment.end_ts-event_segment.start_ts)//1000
        dirpath = self.path_prefix / Path(self.frame_timestamp_to_dirstr(event_segment.start_ts))
        dirpath_json = dirpath / Path(f"json")
        dirpath_json.mkdir(parents=True, exist_ok=True)
        filename_base=f"{source}_{time_str}_{duration_s}s_{len(event_segment.events_list)}_events"
        print(f"Event segment complete, capturing video at {dirpath}/{filename_base}")
        m3u8_content = self.mcp_client.get_m3u8(source, int(event_segment.start_ts/1000),int(event_segment.end_ts/1000))
        # Remove all #EXT-UNIX-TIMESTAMP-MS lines from the m3u8 file
        # m3u8 library doesn't support this tag
        m3u8_content = '\n'.join([line for line in m3u8_content.split('\n') if not line.startswith("#EXT-UNIX-TIMESTAMP-MS")])
        playlist = m3u8.loads(m3u8_content)
        for segment in playlist.segments:
            filepath_ts = dirpath / Path(segment.uri)
            filepath_ts.parent.mkdir(parents=True, exist_ok=True)
            video_name = filepath_ts.relative_to(filepath_ts.parent.parent)
            self.mcp_client.download_video(source, video_name, filepath_ts)
        vidfile = dirpath / Path(f"{filename_base}.m3u8")
        with open(vidfile, "w") as file:
            file.write(m3u8_content)
        json_file = dirpath_json / Path(f"{filename_base}.json")
        event_segment.write_json(json_file)
        if self.annotator:
            self.annotator.create_annotation(json_file, vidfile)

    # This method is called when a media event is received from the MCP
    def handle_media_event_callback(self, media_event, sourceId):
        # Get the type and message of the media event
        type = media_event.get("type", "unknown")
        msg = media_event.get("msg", "unknown")
        # If the media event is a video_file_closed event, add it to the current event segment
        # for the source ID, or to the completed event segments if it's already completed
        if type == "video_file_closed":
            if sourceId in self.current_event_seg:
                event_seg = self.current_event_seg[sourceId]
                event_seg.videos.append(media_event)
            completed_event_segments = self.completed_event_seg.get(sourceId, [])
            for event_seg in completed_event_segments:
                event_seg.videos.append(media_event)
                self.event_segment_complete(sourceId, event_seg)
                self.completed_event_seg[sourceId].remove(event_seg)



    def json_callback(self, data):
        sourceId = data.get("sourceId", "unknown")
        mediaEvents = data.get("mediaEvents", {})
        for event in mediaEvents:
            self.handle_media_event_callback(event, sourceId)

        if self.use_events:
            if 'sensorEvents' in data:
                start_ts = data['frameTimestamp']
                # The end timestamp for all active events
                end_ts = None
                event_in_progress = False
                for sensor in data['sensorEvents']:
                    for id in data['sensorEvents'][sensor]:
                        for event in data['sensorEvents'][sensor][id]:
                            if 'startedAt' in event and event['startedAt'] < start_ts:
                                start_ts = event['startedAt']
                            if 'endedAt' in event:
                                if end_ts is None or event['endedAt'] > end_ts:
                                    end_ts = event['endedAt']
                            else:
                                event_in_progress = True
                if event_in_progress:
                    if not data['sourceId'] in self.current_event_seg:
                        self.current_event_seg[data['sourceId']] = EventSegment(start_ts)
                elif data['sourceId'] in self.current_event_seg:
                    current_event_seg = self.current_event_seg[data['sourceId']]
                    current_event_seg.events_list.append(data)
                    current_event_seg.end_ts = data['frameTimestamp'] if end_ts is None else end_ts
                    if end_ts is not None:
                        self.new_event_segment(data['sourceId'], current_event_seg)
                    del self.current_event_seg[data['sourceId']]
            if data['sourceId'] in self.current_event_seg:
                self.current_event_seg[data['sourceId']].events_list.append(data)
        else:
            if 'frameTimestamp' in data and 'sourceId' in data and \
                data['sourceId'] in self.current_event_seg:
                current_event_seg = self.current_event_seg[data['sourceId']]
                if data['frameTimestamp'] - current_event_seg.start_ts > \
                        self.group_events_max_length :
                    print(f"Event length exceeded {self.group_events_max_length} ms, restarting event segment")
                    self.new_event_segment(data['sourceId'],current_event_seg)
                    del self.current_event_seg[data['sourceId']]

                elif data['frameTimestamp'] - current_event_seg.end_ts > \
                        self.group_events_separation_ms :
                    print(f"More than {self.group_events_separation_ms} ms between events, restarting event segment")
                    print(f"Current frame timestamp is {self.frame_timestamp_to_timestr(data['frameTimestamp'])}"\
                            f" last event timestamp was {self.frame_timestamp_to_timestr(current_event_seg.end_ts)}")
                    self.new_event_segment(data['sourceId'],current_event_seg)
                    del self.current_event_seg[data['sourceId']]

                if 'metaClasses' in data and 'sourceId' in data:
                    if not self.roi_filter or self.roi_filter.objects_in_roi(data):
                        if not data['sourceId'] in self.current_event_seg:
                            self.current_event_seg[data['sourceId']] = EventSegment(data['frameTimestamp'])
                        current_event_seg = self.current_event_seg[data['sourceId']]
                        current_event_seg.events_list.append(data)
                        current_event_seg.end_ts = data['frameTimestamp']

    def start(self):
        self.path_prefix.mkdir(parents=True, exist_ok=True)
        self.listener = AMQPListener(self.amqp_conf)
        self.listener.set_callback(self.json_callback)
        self.listener.start()


    def stop(self):
        if self.listener:
            self.listener.stop()

    def main(self):
        self.start()
        signal.signal(signal.SIGINT, self.signal_handler)
        while True:
            signal.pause()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Host name or IP")
    parser.add_argument("--capture_dir", help="Directory to store captured video (default is " + MCPEventAnnotator.DEFAULT_CAPTURE_DIR + ")")
    parser.add_argument("--sensors_json", help="sensors.json to use for RIO filtering")
    parser.add_argument("--mcp_username", help="Username for MCP", default="root")
    parser.add_argument("--mcp_password", help="Password for MCP", default="root")
    parser.add_argument("--use_events", help="Use only event generator events to select recording intervals", action='store_true')
    parser.add_argument("--annotate", help="Create annotated video after event completion", action='store_true')
    args = parser.parse_args()
    events = MCPEvents(args)
    events.main()


