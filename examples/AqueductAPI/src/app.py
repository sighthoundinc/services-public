from flask_restx import Resource, Api, fields, Namespace
from flask import Flask, request
from flask_cors import CORS
import socket
from lib.Aqueduct import AqueductAMQP, Pipelines, subscribe
import os
import logging

FLASK_PORT = os.getenv('FLASK_PORT', '8888')
AMPQ_HOST = os.getenv('AMPQ_HOST', 'rabbitmq')
AMPQ_PORT = os.getenv('AMPQ_PORT', '5672')
AMPQ_USER = os.getenv('AMPQ_USER', 'guest')
AMPQ_PASSWORD = os.getenv('AMPQ_PASSWORD', 'guest')

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
api = Api(app, version='1.0', title='Pipeline API', description='API for Managing Pipelines')
ns = api.namespace('pipelines', description='Pipeline operations')

pipeline_start_model = api.model('Start Pipeline', {
    'sourceId': fields.String(required=True, description='Source ID'),
    'pipeline': fields.String(required=True, description='Pipeline Name'),
    'URL': fields.String(required=True, description='RTSP URL'),
    'extra_parameters': fields.Raw(description='Extra Parameters'),
})

pipeline_stop_model = api.model('Stop Pipeline', {
    'sourceId': fields.String(required=True, description='Source ID to stop'),
})

# Due to pika restrictions we need one connection per thread
send_publisher = AqueductAMQP("send", AMPQ_HOST, AMPQ_PORT, AMPQ_USER, AMPQ_PASSWORD, logger)
subscribe_publisher = AqueductAMQP("subscribe", AMPQ_HOST, AMPQ_PORT, AMPQ_USER, AMPQ_PASSWORD, logger)

pipelines_manager = Pipelines(".", "./db.json", send_publisher, logger)

@ns.route('/start')
class StartPipeline(Resource):
    @ns.expect(pipeline_start_model, validate=True)
    def post(self):
        data = request.json
        source_id = data['sourceId']
        if pipelines_manager.exists(source_id):
            return {'message': f'Pipeline {source_id} already exists.'}, 400
        if data['pipeline'] not in ["VehicleAnalytics", "TrafficAnalytics"]:
            return {'message': f'Pipeline {data["pipeline"]} not supported.'}, 400
        pipelines = {
            source_id: {
                "pipeline": f"./share/pipelines/{data['pipeline']}/{data['pipeline']}RTSP.yaml",
                "parameters": {
                    "VIDEO_IN": data['URL'],
                    "sourceId": source_id,
                    "recordTo": f"/data/sighthound/media/output/video/{source_id}/",
                    "imageSaveDir": f"/data/sighthound/media/output/image/{source_id}/",
                    "amqpHost": "rabbitmq",
                    "amqpPort": "5672",
                    "amqpExchange": "anypipe",
                    "amqpUser": "guest",
                    "amqpPassword": "guest",
                    "amqpErrorOnFailure": "true",
                    **data['extra_parameters']
                }
            }
        }
        # Save to simulated DB
        pipelines_manager.run(pipelines)
        if not pipelines_manager.wait(source_id, ["start", "done"], 20):
            return {'message': f'Pipeline {source_id} failed to start. Latest status {pipelines_manager.status(source_id)}.'}, 500

        return {'message': f'Started pipeline {source_id}. Status: {pipelines_manager.status(source_id)}.'}, 200

@ns.route('/stop')
class StopPipeline(Resource):
    @ns.expect(pipeline_stop_model, validate=True)
    def post(self):
        data = request.json
        source_id = data['sourceId']
        # Remove from simulated DB
        pipelines_manager.stop(source_id)
        if not pipelines_manager.wait(source_id, ["stop", "done"], 20):
            return {'message': f'Pipeline {source_id} failed to stop. Latest status {pipelines_manager.status(source_id)}.'}, 500
        
        return {'message': f'Stopped pipeline {source_id}. Status: {pipelines_manager.status(source_id)}.'}, 200

@ns.route('/delete')
class DeletePipeline(Resource):
    @ns.expect(pipeline_stop_model, validate=True)
    def post(self):
        data = request.json
        source_id = data['sourceId']
        # Remove from simulated DB
        pipelines_manager.delete(source_id)
        return {'message': f'Deleted pipeline {source_id}.'}, 200

@ns.route('/status')
class Status(Resource):
    def get(self):
        return pipelines_manager.getDB()

@ns.route('/status/<string:sourceId>')
class StatusById(Resource):
    def get(self, sourceId):
        return pipelines_manager.status(sourceId)
    
@api.route('/health')
class Health(Resource):
    def get(self):
        return {'message': 'Ok'}, 200
    
def onAqueductUpdate(ch, method, properties, body):
        pipelines_manager.handle_message(True, method, properties, body)

def setup():
    socket.gethostbyname(AMPQ_HOST)
    send_publisher.connect()
    subscribe_publisher.connect()
    subscribe(subscribe_publisher, onAqueductUpdate, background=True, exchange="aqueduct", topic='everything')
     
if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=FLASK_PORT)