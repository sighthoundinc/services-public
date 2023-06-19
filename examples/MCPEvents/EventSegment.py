class EventSegment:
    def __init__(self, start_ts):
        self.start_ts = start_ts
        self.events_list = []
        self.end_ts = start_ts

