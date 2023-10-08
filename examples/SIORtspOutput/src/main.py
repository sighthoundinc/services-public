#!/usr/bin/env python3
import threading
import RTSPStream as rtsp
import AMQPListener as amqp
from SIODrawer import SIODrawer
from MCP import MCPClient
import os

def get_args():
    rtsp_conf, amqp_conf, mcp_conf = {}, {}, {}
    rtsp_conf["device_id"] = os.environ.get("DEVICE_ID", "my_device")
    rtsp_conf["fps"] = os.environ.get("FPS", 10)
    rtsp_conf["image_width"] = os.environ.get("IMAGE_WIDTH", 640)
    rtsp_conf["image_height"] = os.environ.get("IMAGE_HEIGHT", 480)
    rtsp_conf["port"] = os.environ.get("PORT", 8554)
    rtsp_conf["stream_uri"] = os.environ.get("STREAM_URI", "/live")
    print ("RTSP configuration:", rtsp_conf)
    amqp_conf["host"] = os.environ.get("AMQP_HOST", "localhost")
    amqp_conf["port"] = os.environ.get("AMQP_PORT", 5672)
    amqp_conf["exchange"] = os.environ.get("AMQP_EXCHANGE", "anypipe")
    amqp_conf["routing_key"] = os.environ.get("AMQP_ROUTING_KEY", "#")
    print ("AMQP configuration:", amqp_conf)
    mcp_conf["host"] = os.environ.get("MCP_HOST", "mcp")
    mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
    mcp_conf["username"] = os.environ.get("MCP_USERNAME", None)
    mcp_conf["password"] = os.environ.get("MCP_PASSWORD", None)
    return rtsp_conf, amqp_conf, mcp_conf

def main():
    # getting the required information from the user 
    rtsp_conf, amqp_conf, mcp_conf = get_args()
    # Create an RTSP stream
    stream = rtsp.GstServer(rtsp_conf)
    sio_factory = stream.get_factory()
    # Create an AMQP listener
    amqp_listener = amqp.AMQPListener(amqp_conf)
    # Create MCP Client
    mcp_client = MCPClient(mcp_conf)
    # Create SIO Drawer Callback
    sio_drawer = SIODrawer(mcp_client, stream_factory=sio_factory)
    # Register the callback
    amqp_listener.set_callback(sio_drawer.stream_callback)
    def start_amqp():
        amqp_listener.start()
        stream.stop()
    # Start the stream and the listener in parallel
    amqp_thread = threading.Thread(target=start_amqp)
    amqp_thread.start()
    stream.start()
    amqp_thread.join()
    print("Exiting...")
    
    

if __name__ == "__main__":
    main()