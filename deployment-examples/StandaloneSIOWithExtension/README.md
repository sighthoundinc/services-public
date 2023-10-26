# Standalone Folder Watcher Deployment of SIO

In this example, SIO is deployed in a stand-alone manner, without a RabbitMQ broker or client processing the results.
Instead, a pipeline extension is used to process and report the pipeline output.

Contact [support@sighthound.com](mailto:support@sighthound.com) with any questions, and visit our [Developer Portal](https://dev.sighthound.com) for more information.


## Running the sample

Before getting started, you must copy your `sighthound-license.json` into the `./StandaloneSIOWithExtension/config/` folder. If you do not have a license, please contact [support@sighthound.com](mailto:support@sighthound.com).

Ensure `./StandaloneSIOWithExtension/data/input` exists prior to starting the service.

Next, open a terminal, `cd` into the `./StandaloneSIOWithExtension/` folder, and run the following command to start the services:

```bash
docker compose up -d
```

If you have an NVIDIA GPU installed and properly configured, you can run the following command instead to enable GPU acceleration:

```bash
SIO_DOCKER_RUNTIME=nvidia docker compose up -d
```

You can then deposit images and videos into `./StandaloneSIOWithExtension/data/input` and watch the output being printed as those are being procesed.

