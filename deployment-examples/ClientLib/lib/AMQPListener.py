#!/usr/bin/env python
import pika, json
import traceback
import socket

class AMQPListener:
    host = 'localhost'
    exchange = 'anypipe'
    routing_key = '#'
    port = 5672

    def __init__(self,conf):
        self.queue_name = None
        self.channel = None
        self.connection = None
        self.json_callback = None
        self.host = conf.get("host", AMQPListener.host)
        self.exchange = conf.get("exchange", AMQPListener.exchange)
        self.routing_key = conf.get("routing_key", AMQPListener.routing_key)
        self.port = conf.get("port", AMQPListener.port)
        self.json_callback = lambda data: print(f"Received data {data}")

    def set_callback(self, json_callback):
        self.json_callback = json_callback

    def connect(self):
        if not self.connection:
            self.connection = pika.BlockingConnection(
                        pika.ConnectionParameters(host=self.host,port=self.port))
            self.channel = self.connection.channel()

            self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic', durable=True)

    def get_queue_name(self):
        if not self.queue_name:
            self.connect()
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
        print(f"Using queue name {self.queue_name}")
        return self.queue_name

    def callback(self,ch, method, properties, body):
        try:
            data = json.loads(body)
            if self.json_callback:
                self.json_callback(data)
        except Exception as e:
            print(f"Caught exception {e} handling callback")
            traceback.print_exc()

    def start(self):
        """
        Start the amqp listener, setting up a callback at @param json_callback
        function with single argument representing a JSON payload.
        """
        print(f"Starting AMQP Listener on {self.host}:{self.port}")
        try:
            self.connect()
        except socket.gaierror as e:
            traceback.print_exc()
            print(f"Error connecting to AMQP host: {self.host}:{self.port}. {e}.")
            print("Please check your AMQP configuration. Did you start RabbitMQ?")
            print("You can also use the environment variables AMQP_HOST and AMQP_PORT to configure the host and port.")
            return
        except Exception as e:
            traceback.print_exc()
            print(f"Caught exception '{e}' connecting to AMQP")
            return
        queue_name = self.get_queue_name()
        self.channel.queue_bind(exchange=self.exchange, queue=queue_name,
                                routing_key=self.routing_key)
        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self.callback, auto_ack=True)
        print(' [*] Listening for AMQP messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def stop(self):
        self.channel.stop_consuming()
