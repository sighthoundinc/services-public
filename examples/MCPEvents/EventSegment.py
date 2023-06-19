import os
import json

class EventSegment:
    def __init__(self, start_ts):
        self.start_ts = start_ts
        self.events_list = []
        self.end_ts = start_ts
        self.videos = []

    def write_json(self, path):
        with open(path, 'w') as f:
            json.dump(self, f, indent=4, default=vars)
