#!/usr/bin/env python3
import threading
import AMQPListener as amqp
from MCP import MCPClient
from SIO import SIO
import os

def get_args():
    amqp_conf, mcp_conf, db_conf = {}, {}, {}
    amqp_conf["host"] = os.environ.get("AMQP_HOST", "rabbitmq_svc")
    amqp_conf["port"] = os.environ.get("AMQP_PORT", 5672)
    amqp_conf["exchange"] = os.environ.get("AMQP_EXCHANGE", "sio")
    amqp_conf["routing_key"] = os.environ.get("AMQP_ROUTING_KEY", "#")
    print ("AMQP configuration:", amqp_conf)
    mcp_conf["host"] = os.environ.get("MCP_HOST", "mcp_svc")
    mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
    mcp_conf["username"] = os.environ.get("MCP_USERNAME", None)
    mcp_conf["password"] = os.environ.get("MCP_PASSWORD", None)
    print ("MCP configuration:", amqp_conf)
    db_conf["path"] = os.environ.get("DB_PATH", "/data/sighthound/db/lpdb.sqlite")
    return amqp_conf, mcp_conf, db_conf


def main():
    # getting the required information from the user
    amqp_conf, mcp_conf, db_conf = get_args()
    # Create an AMQP listener
    amqp_listener = amqp.AMQPListener(amqp_conf)
    # Create MCP Client
    mcp_client = MCPClient(mcp_conf)
    # Create SIO Client
    sio_client = SIO(mcp_client, db_conf)
    # Register the callback
    amqp_listener.set_callback(sio_client.callback)
    def start_amqp():
        sio_client.initDbConnection()
        amqp_listener.start()
    # Start the stream and the listener in parallel
    amqp_thread = threading.Thread(target=start_amqp)
    amqp_thread.start()
    amqp_thread.join()
    print("Exiting...")



if __name__ == "__main__":
    main()