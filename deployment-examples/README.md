# Deployment examples

Sample deployments in this folder demonstrate how to accomplish specific tasks using Sighthound utilities without the overhead of managed `services`, with only standard Docker tools and commands at user's disposal.

The following samples are available:

* `ClientLib` - a collection of Python classes to use as base for sample client apps, and shell scripts for running those apps
* `SighthoundRestApiGateway` - a deployment in which `VehicleAnalytics` pipeline is deployed with a REST API gateway in front of it, enabling image annotation API, with an optional UI front end.
* `VideoStreamsConsumer` - a deployment in which `VehicleAnalytics` pipeline consumes multiple video streams from live RTSP sources, and emits analytics output to AMQP broker deployed locally.
* `VideoStreamsRecorder` - similar to `VideoStreamConsumer`, but also generates video recordings and images as part of its analytics output. `MCP` service is deployed for providing access to and managing the generated media