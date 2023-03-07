from curses import cbreak
import threading
import queue
import subprocess
import traceback
import datetime
import time
from urllib import request
import m3u8
from base64 import b64encode


def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'

class MCPFetcher:
    PORT = 9097
    class FetchJob:
        def __init__(self, source, file_path, event_segment):
            self.source = source
            self.file_path = file_path
            self.event_segment = event_segment

    def __init__(self, host, username, password):
        self.host = host
        self.queue = None
        self.username = username
        self.password = password
        self.auth_header_content = basic_auth(username, password)
        self.ffmpeg_authentication = ""
        if username and password:
            self.ffmpeg_authentication = f" -headers \'Authorization: {self.auth_header_content}\' "

    def update_event_segment(self, event_segment, m3u8_url):
        m3u8_request = request.Request(m3u8_url)
        m3u8_request.add_header("Authorization", self.auth_header_content)
        with request.urlopen(m3u8_request) as r:
            m3u8_content = r.read().decode('utf-8')
            print(m3u8_content)
            m3u8_obj = m3u8.loads(m3u8_content)
            print(m3u8_obj)
            event_segment.start_ts = int(m3u8_obj.program_date_time.timestamp()*1000)
            if len(m3u8_obj.segments):
                event_segment.end_ts = int((m3u8_obj.segments[-1].current_program_date_time.timestamp() +
                                        m3u8_obj.segments[-1].duration) * 1000)
    
    def run_ffmpeg(self, command, error_log_file):
        try:
            print(f"Running ffmpeg command {command}")
            subprocess.run(command, shell=True, check= True)

        except subprocess.CalledProcessError as e:
            print(f"Caught exception {e.output} running ffmpeg command {command}")
            with open(error_log_file, "w") as text_file:
                text_file.write(command)
            raise

    def fetch_video(self, fetch_job):
        m3u8_url = f"http://{self.host}:{MCPFetcher.PORT}/hlsfs/source/{fetch_job.source}/{fetch_job.event_segment.start_ts//1000}..{fetch_job.event_segment.end_ts//1000}.m3u8"
        self.update_event_segment(fetch_job.event_segment, m3u8_url)
        command = f'ffmpeg -y {self.ffmpeg_authentication} -i {m3u8_url}'
        command += f" -vcodec copy {fetch_job.file_path}"
        end_ts = datetime.datetime.fromtimestamp(fetch_job.event_segment.end_ts//1000)
        min_seconds_before_fetch = 10
        now = datetime.datetime.today()
        if now < (end_ts + datetime.timedelta(seconds=min_seconds_before_fetch)):
            print(f"Waiting for at least {min_seconds_before_fetch} seconds since end_ts at {end_ts} before attempting fetch")
            time.sleep((end_ts + datetime.timedelta(seconds=min_seconds_before_fetch) - now).total_seconds())
        self.run_ffmpeg(command, str(fetch_job.file_path) + ".failed.ffpmegcmd.txt")


    def fetcher_thread(self):
        while True:
            fetch_job = self.queue.get()
            try:
                self.fetch_video(fetch_job)
                if self.video_callback:
                    self.video_callback(fetch_job.file_path, fetch_job.event_segment)
            except Exception as e:
                print(f"Caught exception {e} handling with ffmpeg record or callback")
                traceback.print_exc()
            self.queue.task_done()

    def start(self, video_callback):
        self.video_callback = video_callback
        self.queue = queue.Queue()
        threading.Thread(target=self.fetcher_thread, daemon=True).start()

    def fetch_video_async(self, source, file_path, event_segment):
        fetch_job = MCPFetcher.FetchJob(source, file_path, event_segment)
        self.queue.put(fetch_job)

