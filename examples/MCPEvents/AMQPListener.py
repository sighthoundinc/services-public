#!/usr/bin/env python
import pika, json
import traceback

class AMQPListener:
    EXCHANGE = 'anypipe'
    ROUTING_KEY = '#'
    PORT = 5672

    def __init__(self,host):
        self.queue_name = None
        self.channel = None
        self.connection = None
        self.json_callback = None
        self.host = host

    def get_queue_name(self):
        if not self.queue_name:
            self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host,port=AMQPListener.PORT))
            self.channel = self.connection.channel()

            self.channel.exchange_declare(exchange=AMQPListener.EXCHANGE, exchange_type='topic', durable=True)

            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
        return self.queue_name

    def callback(self,ch, method, properties, body):
        try:
            data = json.loads(body)
            if self.json_callback:
                self.json_callback(data)
        except Exception as e:
            print(f"Caught exception {e} handling callback")
            traceback.print_exc()

    def start(self, json_callback):
        """
        Start the amqp listener, setting up a callback at @param json_callback
        function with single argument representing a JSON payload.
        """
        self.json_callback = json_callback
        queue_name = self.get_queue_name()
        self.channel.queue_bind(exchange=AMQPListener.EXCHANGE, queue=queue_name,
                                routing_key=AMQPListener.ROUTING_KEY)
        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self.callback, auto_ack=True)
        self.channel.start_consuming()

    def stop(self):
        self.channel.stop_consuming()
