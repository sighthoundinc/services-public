#!/usr/bin/env python3
import AMQPListener as amqp
from MCP import MCPClient
from SIO import SIO
from SIODrawer import SIODrawer
import os

def get_args():
    amqp_conf, mcp_conf = {}, {}
    amqp_conf["host"] = os.environ.get("AMQP_HOST", "localhost")
    amqp_conf["port"] = os.environ.get("AMQP_PORT", 5672)
    amqp_conf["exchange"] = os.environ.get("AMQP_EXCHANGE", "anypipe")
    amqp_conf["routing_key"] = os.environ.get("AMQP_ROUTING_KEY", "#")
    print ("AMQP configuration:", amqp_conf)
    mcp_conf["host"] = os.environ.get("MCP_HOST", "mcp")
    mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
    mcp_conf["username"] = os.environ.get("MCP_USERNAME", None)
    mcp_conf["password"] = os.environ.get("MCP_PASSWORD", None)
    print ("MCP configuration:", mcp_conf)
    return amqp_conf, mcp_conf

def main():
    # getting the required information from the user 
    amqp_conf, mcp_conf = get_args()
    # Create an AMQP listener
    amqp_listener = amqp.AMQPListener(amqp_conf)
    # Create MCP Client
    mcp_client = MCPClient(mcp_conf)
    # SIO Drawer
    sio_drawer = SIODrawer()
    # Register the callback
    sio = SIO(mcp_client, sio_drawer)
    amqp_listener.set_callback(sio.callback)
    amqp_listener.start()
    
if __name__ == "__main__":
    main()