import sqlite3
import os
from datetime import datetime, timedelta

class LicensePlate:
    def __init__(self, object_id, region, plate_string, detection_time, source_id, x, y, w, h, imageId):
        self.object_id = object_id
        self.region = region
        self.plate_string = plate_string
        self.detection_time = detection_time
        self.source_id = source_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.imageId = imageId if imageId else ""

    def to_dict(self):
        return {
            "oid" : self.object_id,
            "string" : self.plate_string,
            "region" : self.region,
            "time" : self.detection_time,
            "sourceId" : self.source_id,
            "rect" : [ self.x, self.y, self.w, self.h ],
            "imageId" : self.imageId
        }

class LicensePlateDB:
    def __init__(self, db_path):
        os.makedirs(os.path.basename(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS plates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id TEXT UNIQUE,
                    region TEXT,
                    plate_string TEXT,
                    detection_time INTEGER,  -- Epoch time
                    source_id TEXT,
                    x INTEGER,
                    y INTEGER,
                    w INTEGER,
                    h INTEGER,
                    imageId STRING
                )
            ''')

    def add_detection(self, license_plate):
        with self.conn:
            self.conn.execute('''
                INSERT OR IGNORE INTO plates (object_id, region, plate_string, detection_time, source_id, x, y, w, h, imageId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id)
                DO UPDATE SET
                region = excluded.region,
                plate_string = excluded.plate_string,
                detection_time = excluded.detection_time,
                x = excluded.x,
                y = excluded.y,
                w = excluded.w,
                h = excluded.h,
                imageId = excluded.imageId;
                ''', (
                license_plate.object_id, license_plate.region, license_plate.plate_string,
                int(license_plate.detection_time), license_plate.source_id,
                license_plate.x, license_plate.y, license_plate.w, license_plate.h,
                license_plate.imageId
            ))

    def delete_by_age(self, max_age_days):
        cutoff_time = int((datetime.now() - timedelta(days=max_age_days)).timestamp())
        with self.conn:
            self.conn.execute('''
                DELETE FROM plates WHERE detection_time < ?
            ''', (cutoff_time,))

    def get_most_recent(self, count):
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM plates ORDER BY detection_time DESC LIMIT ?
        ''', (count,))
        rows = cur.fetchall()
        return [LicensePlate(*row[1:]) for row in rows]

    def get_by_time_range(self, start_time, end_time):
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM plates
            WHERE detection_time BETWEEN ? AND ?
            ORDER BY detection_time DESC
        ''', (int(start_time), int(end_time)))
        rows = cur.fetchall()
        return [LicensePlate(*row[1:]) for row in rows]

    def get_by_plate_string(self, plate_string, start_time=None, end_time=None):
        cur = self.conn.cursor()
        if not start_time is None and not end_time is None:
            cur.execute('''
                SELECT * FROM plates
                WHERE plate_string LIKE ? AND detection_time BETWEEN ? AND ?
                ORDER BY detection_time DESC
            ''', (plate_string,int(start_time),int(end_time)))
        else:
            cur.execute('''
                SELECT * FROM plates WHERE plate_string LIKE ?
            ''', (plate_string,))
        rows = cur.fetchall()
        return [LicensePlate(*row[1:]) for row in rows]

    def close(self):
        self.conn.close()

# Usage example:
if __name__ == '__main__':
    db = LicensePlateDB('license_plates.db')

    # Create a new LicensePlate object
    current_time = int(datetime.now().timestamp())
    license_plate = LicensePlate(
        object_id='123ABC',
        region='FL',
        plate_string='ABC1234',
        detection_time=current_time,
        source_id='source-1',
        x=50, y=100, w=200, h=300,
        imageId="0"
    )

    # Adding a new detection
    db.add_detection(license_plate)

    # Update a detection
    license_plate.region = 'CA'
    license_plate.plate_string = 'XYZ5678'
    db.update_detection(license_plate)

    # Query for the 5 most recent detections
    recent_detections = db.get_most_recent(5)
    for detection in recent_detections:
        print(vars(detection))

    # Query for detections in a time range
    start_time = int(datetime(2024, 8, 1).timestamp())
    end_time = int(datetime(2024, 8, 20).timestamp())
    detections_in_range = db.get_by_time_range(start_time, end_time)
    for detection in detections_in_range:
        print(vars(detection))

    # Query for detections with a specific plate string
    specific_detections = db.get_by_plate_string('XYZ5678')
    for detection in specific_detections:
        print(vars(detection))

    # Delete detections older than 30 days
    db.delete_by_age(30)

    db.close()
