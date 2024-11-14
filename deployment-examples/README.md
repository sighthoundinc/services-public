# Deployment examples

Sample deployments in this folder demonstrate how to accomplish specific tasks using Sighthound utilities without the overhead of managed `services`, with only standard Docker tools and commands at user's disposal.

The following samples are available:

* `ALPRDemo` - an end-to-end sample for live stream and watched folder analytics, an analytics output consumer, simple database integration, and REST API for querying the generated results, and a wxPython UI for visualizing the output.
* `ClientLib` - a collection of Python classes to use as base for sample client apps, and shell scripts for running those apps
* `SighthoundRestApiGateway` - a deployment in which `VehicleAnalytics` pipeline is deployed with a REST API gateway in front of it, enabling image annotation API, with an optional UI front end.
* `SIOOnDemandAnalytics` - folder watch/live stream monitoring deployed side-by-side, with a REST gateway in front of both.
* `StandaloneSIOWithExtension` - demonstrates deployment of SIO without message bus integration, using pipeline extensions as a method for an alternative egress (to file/standard output or REST endpoint) and/or additional output filtering.
* `VideoStreamsConsumer` - a deployment in which `VehicleAnalytics` pipeline consumes multiple video streams from live RTSP sources, and emits analytics output to AMQP broker deployed locally.
* `VideoStreamsRecorder` - similar to `VideoStreamConsumer`, but also generates video recordings and images as part of its analytics output. `MCP` service is deployed for providing access to and managing the generated media