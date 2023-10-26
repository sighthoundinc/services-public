# Sighthound Vehicle Analytics REST API

The Sighthound Vehicle Analytics REST API returns detection coordinates and annotations for all vehicles and license plates detected in an image. For vehicles, the annotations include make, model, color, and generation. For license plates, the annotations include the characters from the plate and region (e.g., Florida, Germany, etc.).

This deployment is comprised of 3 services: a REST gateway, SIO's [Vehicle Analytics](https://dev.sighthound.com/sio/pipelines/VehicleAnalytics/), and a browser-based UI demo. The gateway works alongside the SIO Analytics service container, using its [folder watcher pipeline](https://dev.sighthound.com/sio/pipelines/VehicleAnalytics/#vehicleanalyticsfolderwatch) for processing and a folder shared between the two containers for data exchange. The UI demo can be used to quickly and easily upload files to the API and visualize the results.

This guide contains instructions on how to run the Sighthound Vehicle Analytics REST API using Docker Compose. If you prefer to use your own `docker run` command or other orchestration methods, please refer to the `docker-compose.yml` file for the necessary environment variables, configuration files, and volume mounting examples. More fine-tuning is possible both through docker configuration and SIO parameter modifications.

Contact [support@sighthound.com](mailto:support@sighthound.com) with any questions, and visit our [Developer Portal](https://dev.sighthound.com) for more information.


## Running the API

Before getting started, you must copy your `sighthound-license.json` into the `./SighthoundRestApiGateway/config/` folder. If you do not have a license, please contact [support@sighthound.com](mailto:support@sighthound.com).

Next, open a terminal, `cd` into the `./SighthoundRestApiGateway/` folder, and run the following command to start the services:

```bash
docker compose up -d
```

If you have an NVIDIA GPU installed and properly configured, you can run the following command instead to enable GPU acceleration:

```bash
SIO_DOCKER_RUNTIME=nvidia docker compose up -d
```

## UI Demo

Once the containers are running, open the UI demo in a browser at http://localhost:8484. You can submit images through the UI demo by using HTTP/HTTPS links or by uploading files from your local computer. The browser's developer tools allow you to inspect the requests and responses to see how it's communicating with the Sighthound REST API Gateway.

We recommend using the UI Demo for development purposes only, and it should be removed from the docker-compose.yml before deploying to production.

## Request and Response

See the [online documentation](https://dev.sighthound.com/cloud-api/docs/quickstart/docker/#request-format) for details on the request/response formats and code samples.
