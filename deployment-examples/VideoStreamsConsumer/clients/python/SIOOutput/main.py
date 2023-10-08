#!/usr/bin/env python3
import AMQPListener as amqp
from SIO import SIO
import os

def get_args():
    amqp_conf = {}
    amqp_conf["host"] = os.environ.get("AMQP_HOST", "localhost")
    amqp_conf["port"] = os.environ.get("AMQP_PORT", 5672)
    amqp_conf["exchange"] = os.environ.get("AMQP_EXCHANGE", "sio")
    amqp_conf["routing_key"] = os.environ.get("AMQP_ROUTING_KEY", "*")
    print ("AMQP configuration:", amqp_conf)
    return amqp_conf

def main():
    # getting the required information from the user
    amqp_conf = get_args()
    # Create an AMQP listener
    amqp_listener = amqp.AMQPListener(amqp_conf)
    # Register the callback
    sio = SIO()
    amqp_listener.set_callback(sio.callback)
    amqp_listener.start()

if __name__ == "__main__":
    main()