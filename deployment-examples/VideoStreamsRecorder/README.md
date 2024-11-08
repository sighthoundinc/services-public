# Sighthound Vehicle Analytics - RTSP Client generating media output

This sample continues where `VideoStreamConsumer` left off, and adds on media generation by SIO analytics service, with addition of MCP (Media Control Proxy) service for providing media access API and lifecycle managment.

This deployment is comprised of 4 services: SIO's [Vehicle Analytics](https://dev.sighthound.com/sio/pipelines/VehicleAnalytics/), AMQP broker, MCP and an optional RTSP stream provider.

Contact [support@sighthound.com](mailto:support@sighthound.com) with any questions, and visit our [Developer Portal](https://dev.sighthound.com) for more information.


## Configuration

* Most of the relevant configuration, and the entire set of pipeline parameters (including RTSP URIs) is specified in `./config/analytics/pipelines.json`. This file is referenced directly by `docker-compose.yml`'s entrypoint.
* RabbitMQ configuration is available in `./config/rabbitmq` - please do not use it for your production deployment, and ensure that whatever you do use satisfies your network and security requirements.
* The media lifecycle is driven by the configuration in `./config/mcp/mcp.yml`. With configuration specified, older media items will be removed once total size of items generated reaches `2GB`. It is important that RabbitMQ configuration (including exchange and routing key), match those specified for `sio`, otherwise MCP won't be aware of media items being created.

## Running the sample deployment

Before getting started, you must copy your `sighthound-license.json` into the `./VideoStreamRecorder/config/` folder. If you do not have a license, please contact [support@sighthound.com](mailto:support@sighthound.com).

Next, open a terminal, `cd` into the `./VideoStreamRecorder/` folder, and run the following command to start the services:

```bash
docker compose up -d
```

If you have an NVIDIA GPU installed and properly configured, you can run the following command instead to enable GPU acceleration:

```bash
SIO_DOCKER_RUNTIME=nvidia docker compose up -d
```

Or if you have an NVIDIA Tegra device properly configured (e/g DNNcam), you can run the following command instead to enable GPU acceleration:

```bash
SIO_DOCKER_RUNTIME=nvidia SIO_DOCKER_TAG_VARIANT="-r32.7.3-arm64v8" docker-compose up -d
```

## Running the client samples

Once the services are up and running, start the client sample with a `docker compose up` command while inside the relevant sample's folder in `./clients/python/`


## OS Compatibility

`SIO_DOCKER_TAG_VARIANT` environment variable used in `docker-compose` controls the flavor of SIO analytics container image. While on x86 systems thing largely work without setting it, on Jetson-based system, set it to the value most compatible with your base OS.

* `-r32.4.3-arm64v8` (built for hardware running Jetpack 4.4)
* `-r32.7.3-arm64v8` (built for hardware running Jetpack 4.6)
* `-r35.3.1-arm64v8` (work in progress, built for hardware running Jetpack 5.1)
* `-amd64` for x86 based systems

This variable may already be pre-set in more recent releases of ShOS / on Sighthound devices.

