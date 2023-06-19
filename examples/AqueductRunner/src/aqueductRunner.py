#! /usr/bin/env python3
import pika
import sys
import json
import time
import glob
import argparse
import logging
import os
import socket
from datetime import datetime
from threading import Thread
from tabulate import tabulate

logger = logging.getLogger("aqueduct")

parser = argparse.ArgumentParser()

parser.add_argument( '-log',
                    '--loglevel',
                    default='info',
                    help='Provide logging level. Example --loglevel debug, default=info' )
parser.add_argument('--pipelinesDir', "-d",  help='Folder to watch for pipeline files', default='./pipelines')
parser.add_argument('--pipelinesDBFile', help='', default='./db.json')
parser.add_argument('--amqpHost', help='AMQP host', default='rabbitmq')
parser.add_argument('--amqpPort', help='AMQP port', default=5672, type=int)
parser.add_argument('--amqpUserName','-u', help='AMQP username', default='guest')
parser.add_argument('--amqpPassword', '-p', help='AMQP password', default='guest')
parser.add_argument('--amqpExchange', help='AMQP exchange', default='aqueduct')
parser.add_argument('--executeRoutingKey', help='Aqueduct execute routing key', default='aqueduct.execute.default')
parser.add_argument('--controlRoutingKey', help='Aqueduct control key', default='aqueduct.control.default')
parser.add_argument('--statusRoutingKey', help='Aqueduct status key', default='aqueduct.status.#')
parser.add_argument('--everythingRoutingKey', help='Aqueduct status key', default='#')
parser.add_argument('--sleep', help='Sleep time between loops', default=10, type=int)
parser.add_argument('command', help='Command to run', choices=['update', 'folderwatch', 'watch', 'run', 'stop', 'ps'])
parser.add_argument('args', help='Arguments to pass to the command', nargs='*')

def help():
    parser.print_help(sys.stderr)
    sys.exit(1)

def time_ago(time):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    Modified from: http://stackoverflow.com/a/1551394/141084
    """

    if time == 0:
        return 'Never'
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif type(time) is float:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    else:
        raise ValueError('invalid date %s of type %s' % (time, type(time)))
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return 'error'

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(round(second_diff,2)) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( round(second_diff / 60 ,2)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( round(second_diff / 3600 ,2)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(round(day_diff, 2)) + " days ago"
    if day_diff < 31:
        return str(round(day_diff/7,2)) + " weeks ago"
    if day_diff < 365:
        return str(round(day_diff/30, 2)) + " months ago"
    return str(round(day_diff/365,2)) + " years ago"

class Pipelines:
    def __init__(self, path, pipelinesDBFile, publisher, _logger):
        self.path = path
        self.pipelinesDBFile = pipelinesDBFile
        self.logger = _logger.getChild('pipelines')
        self.publisher = publisher
        self.logger.info('Reading pipelines from: %s', self.path)
        if self.path != "":
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            if not os.path.isdir(self.path):
                self.logger.getChild("init").error('Pipelines path does not exist: %s', self.path)
                raise Exception('Pipelines path does not exist: %s', self.path)
        else:
            self.logger.getChild("init").warning('Pipelines path is empty, will not load any pipelines or save pipelines data')

        # Check if db file exists
        if not os.path.isfile(self.pipelinesDBFile):
            self.logger.getChild("init").info('Creating db file: %s', self.pipelinesDBFile)
            with open(self.pipelinesDBFile, 'w') as f:
                f.write('{}')

    def getDB(self):
        if self.path == "":
            return {}
        with open(self.pipelinesDBFile, 'r') as f:
            data = json.load(f)
            return data

    def writeDB(self, data):
        if self.path == "":
            return
        with open(self.pipelinesDBFile, 'w') as f:
            json.dump(data, f, indent=4)

    def handle_message(self, watch_mode, method, props, body):
        routing_key = method.routing_key
        print(f" [x] Received {routing_key}: {body}")
        try:
            message = json.loads(body)
            if routing_key.startswith("aqueduct.status"):
                self.logger.debug(f"Pipeline '{message['sourceId']}' status: {message['cause']}")
                self.updateStatusPipeline(message['sourceId'], message['cause'])
            if watch_mode:
                self.print_pipelines_db(datetime.now().strftime("%H:%M:%S"), self.getDB(), clear=True)
        except Exception as e:
            print(e)


    def ps(self):
        if self.path == "":
            self.logger.getChild("ps").warning('Pipelines path is empty, will not load any pipelines or save pipelines data')
            return
        self.updateDBFromDisk()
        data = self.getDB()
        self.print_pipelines_db("Pipelines", data)


    def updateStatusPipeline(self, id, status):
        if self.path == "":
            return
        pipelines_db = self.getDB()
        if id in pipelines_db:
            self.logger.info(f"Pipeline {id}, changed status from {pipelines_db[id]['status']} to {status}")
            pipelines_db[id]["status"] = status
            pipelines_db[id]['lastStatusUpdate'] = int(datetime.now().timestamp())
        else:
            self.logger.error(f"Pipeline {id} not found in db")
        self.writeDB(pipelines_db)

    def addOrUpdatePipeline(self, id, source, data):
        source = os.path.basename(source).replace('.json', '')
        if self.path == "":
            logger.warn(f"Cannot add or update pipeline {id}")
        pipelines_db = self.getDB()
        lastUpdate = int(datetime.now().timestamp())
        if id in pipelines_db:
            if source != pipelines_db[id]['source']:
                self.logger.error(f"Error while updating {id}, source was added by another file {pipelines_db[id]['source']}, but found in {source}")
            pipelines_db[id]["data"] = data
            pipelines_db[id]["lastUpdate"] = lastUpdate
        else:
            status = "loaded"
            lastStatusUpdate = 0
            created = int(datetime.now().timestamp())
            pipelines_db[id] = {"data": data, "status": status, "lastStatusUpdate": lastStatusUpdate, "lastUpdate": lastUpdate, "created": created, "source": source}

        self.writeDB(pipelines_db)

    def print_pipelines_db(self, title, pipelines_db, clear=False):
        if self.path == "":
            return []
        if clear:
            os.system('cls' if os.name in ('nt', 'dos') else 'clear')
        print(title)
        table = [['Id', 'Status', 'Last Status Update', 'Last Update', 'Created']]
        for id, pipeline  in pipelines_db.items():
            created_str = datetime.fromtimestamp(pipeline['created']).strftime('%m/%d/%Y, %H:%M:%S')
            lastStatusUpdate_str = time_ago(pipeline['lastStatusUpdate'])
            lastUpdate_str = datetime.fromtimestamp(pipeline['lastUpdate']).strftime('%m/%d/%Y, %H:%M:%S')
            table.append([id, pipeline['status'], lastStatusUpdate_str, lastUpdate_str, created_str])
        print(tabulate(table))

    def updateDBFromDisk(self):
        for aqueduct_file in glob.glob(self.path + '/*.json'):
            try:
                with open(aqueduct_file) as f:
                    data = json.load(f)
                    for pipeline in data:
                        self.addOrUpdatePipeline(pipeline, aqueduct_file, data[pipeline])
            except Exception as e:
                self.logger.getChild("updateDBFromDisk").error('Error loading pipeline: %s', aqueduct_file)
                print(e)

    def get(self, id):
        if self.path == "":
            return None
        for pipeline in glob.glob(self.path + '/*.json'):
            try:
                with open(pipeline) as f:
                    data = json.load(f)
                    if id in data:
                        return data[id]
            except:
                self.logger.getChild("get").warning('Failed to load pipeline: %s', pipeline)
        return None

    def runFolderWatch(self):
        if self.path == "":
            self.logger.getChild("runFolder").warning('Pipelines path is empty, will not load any pipelines or save pipelines data')
            return
        self.updateDBFromDisk()

        for id, data in self.getDB().items():
            logger.info("Running pipeline: %s", id)
            self.runPipeline(id, data["data"])

    def run(self, args):
        logger = self.logger.getChild("run")
        if len(args) < 1:
            logger.error('No pipeline file provided')
            logger.info('Example: aqueductRunner run pipeline.json')
            raise Exception('No pipeline file provided')
        elif len(args) > 1:
            logger.error('Too many arguments')
            logger.info('Example: aqueductRunner run pipeline.json')
            return
        print("Running pipelines from : ", args)
        source_file = args[0]
        with open(source_file) as f:
            data = json.load(f)
            for id, pipeline in data.items():
                logger.info("Running pipeline: %s", id)
                self.addOrUpdatePipeline(id, source_file, pipeline)
                self.runPipeline(id, pipeline)

    def runPipeline(self, id, pipeline):
        logger.info("Running pipeline: %s", id)
        msg = pipeline
        msg["command"] = "execute"
        msg["sourceId"] = id
        self.publisher.publish(json.dumps(msg), 'execute', "." + id)
        self.updateStatusPipeline(id, "execute_sent")

    def stopPipeline(self, id):
        logger.info("Stopping pipeline: %s", id)
        msg = {"command": "stop", "sourceId": id}
        self.publisher.publish(json.dumps(msg), 'execute', "." + id)

    def stop(self, args):
        logger = self.logger.getChild("stop")
        if len(args) < 1:
            logger.error('No pipeline file or id provided')
            logger.info('Example: aqueductRunner stop pipeline_id/pipeline.json')
            return
        elif len(args) > 1:
            logger.error('Too many arguments')
            logger.info('Example: aqueductRunner stop pipeline_id/pipeline.json')
            return
        try:
            pipeline = args[0]
            with open(pipeline) as f:
                data = json.load(f)
                for id, pipeline in data.items():
                    logger.info("Stopping pipeline: %s", id)
                    self.stopPipeline(id)
        except:
            self.stopPipeline(args[0])




class Publisher:
    def __init__(self, name, args, logger):
        self.logger = logger.getChild("publisher").getChild(name)
        self._args = args
        self.logger.info(f"Connecting to AMQP on {args.amqpHost}:{args.amqpPort} with user: {args.amqpUserName}...")
        self._params = pika.connection.ConnectionParameters(
            host=args.amqpHost,
            port=args.amqpPort,
            virtual_host='/',
            credentials=pika.credentials.PlainCredentials(args.amqpUserName, args.amqpPassword))
        self._conn = None
        self._channel = None


    def connect(self):
        if not self._conn or self._conn.is_closed:
            self.logger.debug('Connecting to AMQP instance: %s:%s', self._params.host, self._params.port)
            self._conn = pika.BlockingConnection(self._params)
            self._channel = self._conn.channel()
            self._channel.exchange_declare(exchange=self._args.amqpExchange, exchange_type='topic', durable=True)

    def _choose_routing_key(self, topic):
        if topic == "execute":
            return str(self._args.executeRoutingKey)
        elif topic == "control":
            return str(self._args.controlRoutingKey)
        elif topic == "status":
            return str(self._args.statusRoutingKey)
        elif topic == "everything":
            return str(self._args.everythingRoutingKey)
        else:
            raise Exception("Unknown topic: " + topic)

    def _publish(self, msg, routing_key):
        if self._channel is None:
            raise Exception('Not connected to queue')
        self.logger.info('publishing message: \'%s\' to exchange: "%s" and routing_key: "%s"', msg, self._args.amqpExchange, routing_key)
        self._channel.basic_publish(exchange=self._args.amqpExchange,
                                    routing_key=routing_key,
                                    properties=pika.BasicProperties(content_type='application/json'),
                                    body=msg)
        self.logger.debug('message sent: %s', msg)

    def publish(self, msg, topic=None, suffix=""):
        """Publish msg, reconnecting if necessary."""
        routing_key = self._choose_routing_key(topic) + suffix
        try:
            self._publish(msg, routing_key)
        except pika.exceptions.ConnectionClosed:
            self.logger.debug('reconnecting to queue')
            self.connect()
            self._publish(msg, routing_key)

    def subscribe(self, callback, topic=None):
        self.logger.debug('subscribing to "%s":"%s"', self._args.amqpExchange, self._choose_routing_key(topic))
        if self._channel is None:
            self.logger.error('channel is not initialized')
            return
        queue = self._channel.queue_declare(queue='', exclusive=True)
        self._channel.queue_bind(exchange=self._args.amqpExchange,
                                 queue=queue.method.queue,
                                 routing_key=self._choose_routing_key(topic))
        self._channel.basic_consume(queue=queue.method.queue,
                                    on_message_callback=callback,
                                    auto_ack=True)
        self._channel.start_consuming()

    def close(self):
        if self._conn and self._conn.is_open:
            self.logger.debug('closing queue connection')
            self._conn.close()

def subscribe(publisher, callback, background=True, topic='status'):
    if background:
        T = Thread(target = publisher.subscribe, args = (callback, topic))
        # change T to daemon
        T.setDaemon(True)
        # starting of Thread T
        T.start()
    else:
        publisher.subscribe(callback, topic)

def main(args, logger):
    logger.debug('Starting aqueduct runner...')    

    try:
        socket.gethostbyname(args.amqpHost)
    except socket.gaierror:
        logger.error('Failed to connect to AMQP host: %s', args.amqpHost)
        return
    # Due to pika restrictions we need one connection per thread
    send_publisher = Publisher("send", args, logger)
    subscribe_publisher = Publisher("subscribe", args, logger)
    try:
        send_publisher.connect()
        subscribe_publisher.connect()
    except Exception as e:
        logger.error('Failed to connect to AMQP: %s', e)
        return

    pipelines = Pipelines(args.pipelinesDir, args.pipelinesDBFile, send_publisher, logger)
    watch_mode = args.command in ['watch', 'folderwatch']
    def onAqueductUpdate(ch, method, properties, body):
        pipelines.handle_message(watch_mode, method, properties, body)

    if args.command == 'update':
        logger.info('Running update once...')
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, topic='everything')
        pipelines.runFolderWatch()
        time.sleep(args.sleep)
    elif args.command == 'watch':
        logger.info('Running in watch mode...')
        pipelines.print_pipelines_db(datetime.now().strftime("%H:%M:%S"), pipelines.getDB(), clear=True)
        subscribe(subscribe_publisher, onAqueductUpdate, background=False, topic='everything')

    elif args.command == 'folderwatch':
        logger.info('Running in folderwatch mode...')
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, topic='everything')
        # Send constant updates
        while True:
            pipelines.print_pipelines_db(datetime.now().strftime("%H:%M:%S"), pipelines.getDB(), clear=True)
            pipelines.runFolderWatch()
            logger.debug('Sleeping for %s seconds', args.sleep)
            time.sleep(args.sleep)
    elif args.command == 'run':
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, topic='everything')
        logger.info('Running pipeline')
        pipelines.run(args.args)
        time.sleep(args.sleep)
    elif args.command == 'stop':
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, topic='everything')
        logger.info('Stopping pipeline')
        pipelines.stop(args.args)
        time.sleep(args.sleep)
    elif args.command == 'ps':
        logger.debug('Listing pipelines')
        pipelines.ps()
    else:
        logger.error('Unimplemented command: %s', args.command)
        help()

    logger.debug('Shutting down...')

    # send_publisher.close()
    # subscribe_publisher.close()
    logger.debug('Exiting aqueduct runner...')

#===========================================================================================

if __name__ == "__main__":

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel.upper(), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.getLogger('pika').setLevel(logging.WARNING)

    main(args, logger)