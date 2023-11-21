import pika
import json
import time
import glob
import logging
import os
from datetime import datetime
from threading import Thread
from tabulate import tabulate

logger = logging.getLogger("aqueduct")

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
    def anypipe_message(self, method, props, body, json_file):
        routing_key = method.routing_key
        print(f" [x] Received {routing_key}: {body}")
        try:
            message = json.loads(body)
            if json_file != "":
                # Append message to json file
                with open(json_file, 'a') as f:
                    f.write(json.dumps(message) + "\n")
        except Exception as e:
            print(e)

    def exists(self, id):
        pipelines_db = self.getDB()
        return id in pipelines_db

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

    def run_from_file(self, source_file):
        with open(source_file) as f:
            data = json.load(f)
            self.run(data, source_file)

    def run(self, pipelines, source="unknown"):
        logger = self.logger.getChild("run")
        print("Running pipelines from: ", source)
        for id, pipeline in pipelines.items():
            logger.info("Running pipeline: %s", id)
            self.addOrUpdatePipeline(id, source, pipeline)
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
        self.updateStatusPipeline(id, "stop_sent")

    def deletePipeline(self, id):
        logger.info("Deleting pipeline: %s", id)
        try:
            self.stopPipeline(id)
        except Exception as e:
            print(e)
        self.getDB().pop(id, None)
        self.writeDB(self.getDB())

    def status(self, id):
        pipelines_db = self.getDB()
        if id in pipelines_db:
            return pipelines_db[id]['status']
        else:
            return "not found"

    def waitPipeline(self, id, waitFor, timeout):
        logger.info("Waiting for pipeline: %s, timeout: %d", id, timeout)
        t0 = time.time()
        while True:
            if timeout > 0 and time.time() - t0 > timeout:
                logger.error("Timeout waiting for pipeline: %s", id)
                return False
            pipelines_db = self.getDB()
            if id not in pipelines_db:
                logger.error("Wait: Pipeline not found: %s", id)
                return False
            if pipelines_db[id]['status'] in waitFor:
                logger.info("Wait: Pipeline %s: %s", pipelines_db[id]['status'], id )
                return True
            else:
                logger.info("Wait pipeline '%s' status: %s", id, pipelines_db[id]['status'])
            time.sleep(1)

    def stop(self, pipeline):
        logger = self.logger.getChild("stop")
        try:
            with open(pipeline) as f:
                data = json.load(f)
                for id, pipeline in data.items():
                    logger.info("Stopping pipeline: %s", id)
                    self.stopPipeline(id)
        except:
            self.stopPipeline(pipeline)

    def wait(self, pipeline, waitFor, timeout):
        logger = self.logger.getChild("wait")
        if os.path.isfile(pipeline):
            with open(pipeline) as f:
                data = json.load(f)
                for id, pipeline in data.items():
                    logger.info("Waiting for pipeline: %s", id)
                    return self.waitPipeline(id, waitFor, timeout)
        else:
            return self.waitPipeline(pipeline, waitFor, timeout)
        
    def delete(self, pipeline):
        logger = self.logger.getChild("delete")
        if os.path.isfile(pipeline):
            with open(pipeline) as f:
                data = json.load(f)
                for id, pipeline in data.items():
                    logger.info("Deleting pipeline: %s", id)
                    self.deletePipeline(id)
        else:
            self.deletePipeline(pipeline)

class AqueductAMQP:
    def __init__(self, name, amqpHost, amqpPort, amqpUsername, amqpPassword, logger):
        self.logger = logger.getChild("aqueduct-amqp").getChild(name)
        self.logger.info(f"Connecting to AMQP on {amqpHost}:{amqpPort} with user: {amqpUsername}...")
        self._params = pika.connection.ConnectionParameters(
            host=amqpHost,
            port=amqpPort,
            virtual_host='/',
            credentials=pika.credentials.PlainCredentials(amqpUsername, amqpPassword))
        self._conn = None
        self._channel = None


    def connect(self):
        if not self._conn:
            self.logger.info('Connecting to AMQP instance: %s:%s', self._params.host, self._params.port)
        else:
            self.logger.info(f'Reconnecting to AMQP instance: {self._params.host}:{self._params.port} ...')
            if not self._conn.is_closed:
                self._conn.close()

        self._conn = pika.BlockingConnection(self._params)
        self._channel = self._conn.channel()
        self._channel.exchange_declare(exchange="aqueduct", exchange_type='topic', durable=True)
        


    def _choose_routing_key(self, topic):
        if topic == "execute":
            return 'aqueduct.execute.default'
        elif topic == "control":
            return 'aqueduct.control.default'
        elif topic == "status":
            return 'aqueduct.status.#'
        elif topic == "everything":
            return '#'
        else:
            raise Exception("Unknown topic: " + topic)

    def _publish(self, msg, routing_key):
        if self._channel is None:
            raise Exception('Not connected to queue')
        self.logger.info('publishing message: \'%s\' to exchange: "%s" and routing_key: "%s"', msg, 'aqueduct', routing_key)
        self._channel.basic_publish(exchange='aqueduct',
                                    routing_key=routing_key,
                                    properties=pika.BasicProperties(content_type='application/json'),
                                    body=msg)
        self.logger.debug('message sent: %s', msg)

    def publish(self, msg, topic=None, suffix=""):
        """Publish msg, reconnecting if necessary."""
        routing_key = self._choose_routing_key(topic) + suffix
        try:
            self._publish(msg, routing_key)
        except (pika.exceptions.ConnectionClosed, pika.exceptions.StreamLostError):
            self.connect()
            self._publish(msg, routing_key)

    def subscribe(self, callback, exchange="aqueduct", topic=None):
        self.logger.debug('subscribing to "%s":"%s"', exchange, self._choose_routing_key(topic))
        if self._channel is None:
            self.logger.error('channel is not initialized')
            return
        queue = self._channel.queue_declare(queue='', exclusive=True)
        self._channel.queue_bind(exchange=exchange,
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

def subscribe(publisher, callback, background=True, exchange="aqueduct", topic='status'):
    if background:
        T = Thread(target = publisher.subscribe, args = (callback, exchange, topic))
        # change T to daemon
        T.setDaemon(True)
        # starting of Thread T
        T.start()
    else:
        publisher.subscribe(callback, exchange, topic)