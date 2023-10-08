import threading
import gi
import cv2
# import required library like Gstreamer and GstreamerRtspServer
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject
import numpy as np

loop = GObject.MainLoop()
GObject.threads_init()
Gst.init([])

# Sensor Factory class which inherits the GstRtspServer base class and add
# properties to it.
class SighthoundRtspMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, conf):
        self.frame = np.zeros((10, 10, 3), np.uint8)
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.conf = conf
        self.number_frames = 0
        self.fps = self.conf["fps"]
        self.duration = 1 / float(self.fps) * Gst.SECOND  # duration of a frame in nanoseconds
        self.width, self.height, self.channels = self.conf["image_width"], self.conf["image_height"], 3
        self.resize_width, self.resize_height= self.conf["image_width"], self.conf["image_height"]
        self.clear_frame()

        self.frame_on_display = self.frame.copy()
        self.frame_lock = threading.Lock()

    def set_launch_string(self, width, height, fps):
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             f'caps=video/x-raw,format=RGB,width={width},height={height},framerate={fps}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' 
        print("$ gst-launch-1.0", self.launch_string)

    def update_frame(self):
        with self.frame_lock:
            self.frame_on_display = self.frame.copy()

    def set_frame_size(self, width, height):
        if width != self.width or height != self.height:
            self.width, self.height = width, height
            self.clear_frame()
            self.set_launch_string(self.width, self.height, self.fps)

    def set_current_frame(self, frame):
        self.frame = frame

    def clear_frame(self, color=None):
        if color is not None:
            self.frame = np.full((self.height, self.width, self.channels), color, np.uint8)
        else:
            self.frame = np.zeros((self.height, self.width, self.channels), np.uint8)
    
    def resize_frame(self):
        # It is better to change the resolution of the camera 
        # instead of changing the image shape as it affects the image quality.
        self.frame = cv2.resize(self.frame, (self.resize_width, self.resize_height), \
            interpolation = cv2.INTER_LINEAR)

    def add_frame_number(self):
        self.write_text(str(self.number_frames), location="top_right")
        print("Frame number: ", self.number_frames)

    def write_text(self, text, location="top_left", color=(0, 255, 0), font_scale=1, thickness=2):
        if location == "bottom_left":
            x = 10
            y = self.height - 10
        elif location == "top_left":
            x = 10
            y = 30
        elif location == "center":
            x = int(self.width / 2)
            y = int(self.height / 2)
        else:
            print("Invalid location. Using top_left")
            x = 10
            y = 30
        cv2.putText(self.frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    # method to capture the video feed from the camera and push it to the
    # streaming buffer.
    def on_need_data(self, src, length):
        self.number_frames += 1
        # self.add_frame_number()
        self.resize_frame()
        with self.frame_lock:
            data = self.frame_on_display.tostring()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        
        retval = src.emit('push-buffer', buf)
        # print(f'pushed buffer, frame {self.number_frames}, duration {self.duration} ns, durations {self.duration / Gst.SECOND} s')

        if retval != Gst.FlowReturn.OK:
            print(retval)
    # attach the launch string to the override method
    def do_create_element(self, url):
        # url [ 'abspath', 'copy', 'decode_path_components', 'family', 'free', 'get_port', 'get_request_uri', 'get_request_uri_with_control', 'host', 'parse', 'passwd', 'port', 'query', 'set_port', 'transports', 'user']
        print('do_create_element called', url.query, url.host)
        self.set_launch_string(self.width, self.height, self.fps)
        self.resize_width, self.resize_height = self.width, self.height
        return Gst.parse_launch(self.launch_string)
    
    # attaching the source element to the rtsp media
    def do_configure(self, rtsp_media):
        # rtsp_media [ 'bind_property', 'bind_property_full', 'chain', 'collect_streams', 'compat_control', 'complete_pipeline', 'connect', 'connect_after', 'connect_data', 'connect_object', 'connect_object_after', 'create_stream', 'disconnect', 'disconnect_by_func', 'do_convert_range', 'do_handle_message', 'do_handle_sdp', 'do_new_state', 'do_new_stream', 'do_prepare', 'do_prepared', 'do_query_position', 'do_query_stop', 'do_removed_stream', 'do_setup_rtpbin', 'do_setup_sdp', 'do_suspend', 'do_target_state', 'do_unprepare', 'do_unprepared', 'do_unsuspend', 'emit', 'emit_stop_by_name', 'find_property', 'find_stream', 'force_floating', 'freeze_notify', 'g_type_instance', 'get_address_pool', 'get_base_time', 'get_buffer_size', 'get_clock', 'get_data', 'get_do_retransmission', 'get_dscp_qos', 'get_element', 'get_latency', 'get_max_mcast_ttl', 'get_multicast_iface', 'get_permissions', 'get_profiles', 'get_properties', 'get_property', 'get_protocols', 'get_publish_clock_mode', 'get_qdata', 'get_range_string', 'get_rate_control', 'get_rates', 'get_retransmission_time', 'get_status', 'get_stream', 'get_suspend_mode', 'get_time_provider', 'get_transport_mode', 'getv', 'handle_sdp', 'handler_block', 'handler_block_by_func', 'handler_disconnect', 'handler_is_connected', 'handler_unblock', 'handler_unblock_by_func', 'has_completed_sender', 'install_properties', 'install_property', 'interface_find_property', 'interface_install_property', 'interface_list_properties', 'is_bind_mcast_address', 'is_eos_shutdown', 'is_floating', 'is_receive_only', 'is_reusable', 'is_shared', 'is_stop_on_disconnect', 'is_time_provider', 'list_properties', 'lock', 'n_streams', 'new', 'newv', 'notify', 'notify_by_pspec', 'override_property', 'parent', 'prepare', 'priv', 'props', 'qdata', 'ref', 'ref_count', 'ref_sink', 'replace_data', 'replace_qdata', 'run_dispose', 'seek', 'seek_full', 'seek_trickmode', 'seekable', 'set_address_pool', 'set_bind_mcast_address', 'set_buffer_size', 'set_clock', 'set_data', 'set_do_retransmission', 'set_dscp_qos', 'set_eos_shutdown', 'set_latency', 'set_max_mcast_ttl', 'set_multicast_iface', 'set_permissions', 'set_pipeline_state', 'set_profiles', 'set_properties', 'set_property', 'set_protocols', 'set_publish_clock_mode', 'set_rate_control', 'set_retransmission_time', 'set_reusable', 'set_shared', 'set_state', 'set_stop_on_disconnect', 'set_suspend_mode', 'set_transport_mode', 'setup_sdp', 'steal_data', 'steal_qdata', 'stop_emission', 'stop_emission_by_name', 'suspend', 'take_pipeline', 'thaw_notify', 'unlock', 'unprepare', 'unref', 'unsuspend', 'use_time_provider', 'watch_closure', 'weak_ref']
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

# Rtsp server implementation where we attach the factory sensor with the stream uri
class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, conf):
        super(GstServer, self).__init__()
        self.conf = conf
        self.factory = SighthoundRtspMediaFactory(self.conf)
        self.factory.set_shared(True)
        self.set_service(self.conf["port"])
        self.get_mount_points().add_factory(self.conf["stream_uri"], self.factory)
        print ("RTSP Server started at rtsp://localhost:" + str(self.conf["port"]) + self.conf["stream_uri"])
        self.attach(None)

    def start(self):
        try:
            loop.run()
        except Exception as e:
            print(e)

    def stop(self):
        loop.quit()
    
    def get_factory(self):
        return self.factory