# AqueductRunner

Aqueduct is a service allowing to dynamically launch and control SIO pipelines. Unlike runPipeline or runPipelineSet, which run a pipeline or a pre-configured set of pipelines respectively, it allows pipeline creation and control from the client.

Here is a simple guide to show you how to use Aqueduct:
## Quickstart

First, we need to select the Aqueduct example and bring up the service.

Open your terminal, then type the following commands:

To select aqueduct as SIO backend:
```bash
./scripts/sh-services select_example sio aqueduct
```
To start th SIO service:
```bash
./scripts/sh-services up sio
```
To navigate into the AqueductRunner directory:
```bash
cd examples/AqueductRunner
```
To build the docker image:
```bash
docker-compose build
```
To run the AqueductRunner service:
```bash
docker-compose run aqueductrunner ps
```
## Viewing the Output
After running the AqueductRunner service, you'll see some output in your terminal. This output shows the status of the services, as well as the details of the pipelines it's monitoring (running or not). An example output might look something like this:

```bash
$ docker-compose run aqueductrunner ps   
2023-05-31 22:52:02,041 - aqueduct.publisher.send - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:52:02,042 - aqueduct.publisher.subscribe - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:52:02,069 - aqueduct.pipelines - INFO - Reading pipelines from: ./pipelines
Pipelines
--------  ------  ------------------  --------------------  --------------------
Id        Status  Last Status Update  Last Update           Created
my-video  loaded  Never               05/31/2023, 22:52:02  05/31/2023, 22:50:25
--------  ------  ------------------  --------------------  --------------------

```

## Running a pipeline
You can also run a pipeline with AqueductRunner. For example, if you want to run the pipeline 'live555.json', you would type the following command:

```bash
docker-compose run aqueductrunner run ./pipelines/live555.json
```
This command will execute the pipeline, and the output will show the progress of the pipeline, including the status changes and any messages published during the pipeline execution.
If the pipeline fails to run for some reason (for example, if 'live555' is not set), the output will reflect this. You can check the status of the pipeline again with the aqueductRunner ps command.

For example:
```bash
$ docker-compose run aqueductrunner run ./pipelines/live555.json
2023-05-31 22:54:38,912 - aqueduct.publisher.send - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:54:38,913 - aqueduct.publisher.subscribe - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:54:38,941 - aqueduct.pipelines - INFO - Reading pipelines from: ./pipelines
2023-05-31 22:54:38,942 - aqueduct - INFO - Running pipeline
Running pipelines from :  ['./pipelines/live555.json']
2023-05-31 22:54:38,943 - aqueduct.pipelines.run - INFO - Running pipeline: my-video
2023-05-31 22:54:38,944 - aqueduct - INFO - Running pipeline: my-video
2023-05-31 22:54:38,944 - aqueduct.publisher.send - INFO - publishing message: '{"pipeline": "./share/pipelines/TrafficAnalytics/TrafficAnalyticsRTSP.yaml", "parameters": {"VIDEO_IN": "rtsp://live555/my-video.mkv", "sourceId": "my-video", "recordTo": "/data/sighthound/media/output/video/my-video/", "imageSaveDir": "/data/sighthound/media/output/image/my-video/", "amqpHost": "rabbitmq", "amqpPort": "5672", "amqpExchange": "anypipe", "amqpUser": "guest", "amqpPassword": "guest", "amqpErrorOnFailure": "true"}, "command": "execute", "sourceId": "my-video"}' to exchange: "aqueduct" and routing_key: "aqueduct.execute.default.my-video"
2023-05-31 22:54:38,946 - aqueduct.pipelines - INFO - Pipeline my-video, changed status from loaded to execute_sent
 [x] Received aqueduct.status.my-video: b'{"cause":"start","command":"event","context":"","event":"pipelineStarting","sourceId":"my-video"}'
2023-05-31 22:54:40,089 - aqueduct.pipelines - INFO - Pipeline my-video, changed status from execute_sent to start
 [x] Received aqueduct.instance.aqueduct: b'{"command":"keepAlive","cseq":"17605","pipelines":{"my-video":null}}'
 [x] Received aqueduct.status.my-video: b'{"cause":"done","command":"event","context":"","event":"pipelineTermination","sourceId":"my-video"}'
2023-05-31 22:54:43,111 - aqueduct.pipelines - INFO - Pipeline my-video, changed status from start to done
 [x] Received aqueduct.instance.aqueduct: b'{"command":"keepAlive","cseq":"17606","pipelines":{}}'
$ docker-compose run aqueductrunner ps                          
2023-05-31 22:54:59,255 - aqueduct.publisher.send - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:54:59,256 - aqueduct.publisher.subscribe - INFO - Connecting to AMQP on rabbitmq:5672 with user: guest...
2023-05-31 22:54:59,285 - aqueduct.pipelines - INFO - Reading pipelines from: ./pipelines
Pipelines
--------  ------  ------------------  --------------------  --------------------
Id        Status  Last Status Update  Last Update           Created
my-video  done    16 seconds ago      05/31/2023, 22:54:59  05/31/2023, 22:50:25
--------  ------  ------------------  --------------------  --------------------
```
In this case the pipeline failed because live555 is not running but `aqueductRunner ps` command shows the right pipeline status.

We can check sio logs to corroborate the result:
```bash
root@dnncam-0000818:/data/sighthound/services/examples/AqueductRunner# docker logs sio-dev --tail 3
23/05/31-16:54:43.108 C <15> [root] Critical pipeline error has occurred: Too many failures (3) attempting to read from media source
23/05/31-16:54:43.109 I <20> [root] AMQPMessageProcessor: [my-video] : 'pipelineTermination' , cause: 'done' 
23/05/31-16:54:43.109 I <20> [root] AMQPMessageProcessor: [my-video] : pipeline exited.
```