#! /usr/bin/env python3
import sys
import time
import argparse
import logging
import socket
from datetime import datetime
from lib.Aqueduct import AqueductAMQP, Pipelines, subscribe

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
parser.add_argument('--amqpUsername','-u', help='AMQP username', default='guest')
parser.add_argument('--amqpPassword', '-p', help='AMQP password', default='guest')
parser.add_argument('--sleep', help='Sleep time between loops', default=10, type=int)
parser.add_argument('--timeout', help='Max timeout for start and stop operations. Zero means infinite', default=0, type=int)
parser.add_argument('--json_dump', help='Dump AMQP messages to json file', default="", type=str)
parser.add_argument('command', help='Command to run', choices=['update', 'folderwatch', 'watch', 'run', 'stop', 'ps'])
parser.add_argument('args', help='Arguments to pass to the command', nargs='*')

def help():
    parser.print_help(sys.stderr)
    sys.exit(1)

def main(args, logger):
    logger.debug('Starting aqueduct runner...')    

    try:
        socket.gethostbyname(args.amqpHost)
    except socket.gaierror:
        logger.error('Failed to connect to AMQP host: %s', args.amqpHost)
        return
    # Due to pika restrictions we need one connection per thread
    send_publisher = AqueductAMQP("send", args.amqpHost, args.amqpPort, args.amqpUsername, args.amqpPassword, logger)
    subscribe_publisher = AqueductAMQP("subscribe", args.amqpHost, args.amqpPort, args.amqpUsername, args.amqpPassword, logger)
    anypipe_publisher = AqueductAMQP("anypipe", args.amqpHost, args.amqpPort, args.amqpUsername, args.amqpPassword, logger)
    try:
        send_publisher.connect()
        subscribe_publisher.connect()
        anypipe_publisher.connect()
    except Exception as e:
        logger.error('Failed to connect to AMQP: %s', e)
        return

    pipelines = Pipelines(args.pipelinesDir, args.pipelinesDBFile, send_publisher, logger)
    watch_mode = args.command in ['watch', 'folderwatch']
    def onAqueductUpdate(ch, method, properties, body):
        pipelines.handle_message(watch_mode, method, properties, body)
    def onAnypipeMessage(ch, method, properties, body):
        pipelines.anypipe_message(method, properties, body, args.json_dump)

    if args.command == 'update':
        logger.info('Running update once...')
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, exchange="aqueduct", topic='everything')
        pipelines.runFolderWatch()
        time.sleep(args.sleep)
    elif args.command == 'watch':
        logger.info('Running in watch mode...')
        pipelines.print_pipelines_db(datetime.now().strftime("%H:%M:%S"), pipelines.getDB(), clear=True)
        subscribe(subscribe_publisher, onAqueductUpdate, background=False, exchange="aqueduct", topic='everything')

    elif args.command == 'folderwatch':
        logger.info('Running in folderwatch mode...')
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, exchange="aqueduct", topic='everything')
        # Send constant updates
        while True:
            pipelines.print_pipelines_db(datetime.now().strftime("%H:%M:%S"), pipelines.getDB(), clear=True)
            pipelines.runFolderWatch()
            logger.debug('Sleeping for %s seconds', args.sleep)
            time.sleep(args.sleep)
    elif args.command == 'run':
        if len(args) < 1:
            logger.error('No pipeline file provided')
            logger.info('Example: aqueductRunner run pipeline.json')
            raise Exception('No pipeline file provided')
        elif len(args) > 1:
            logger.error('Too many arguments')
            logger.info('Example: aqueductRunner run pipeline.json')
            raise Exception('Too many arguments')
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, exchange="aqueduct", topic='everything')
        if args.json_dump != "":
            subscribe(anypipe_publisher, onAnypipeMessage, background=True, exchange="anypipe", topic='everything')
        logger.info('Running pipeline')
        pipelines.run_from_file(args[0])
        pipelines.wait(args[0], args.timeout)
    elif args.command == 'stop':
        if len(args) < 1:
            logger.error('No pipeline file or id provided')
            logger.info('Example: aqueductRunner stop pipeline_id/pipeline.json')
            return
        elif len(args) > 1:
            logger.error('Too many arguments')
            logger.info('Example: aqueductRunner stop pipeline_id/pipeline.json')
            return
        subscribe(subscribe_publisher, onAqueductUpdate, background=True, exchange="aqueduct", topic='everything')
        logger.info('Stopping pipeline')
        pipelines.stop(args[0])
        pipelines.wait(args[0], args.timeout)
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