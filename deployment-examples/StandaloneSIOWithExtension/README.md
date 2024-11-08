# Standalone SIO sample

In this example, SIO is deployed in a stand-alone manner, without a RabbitMQ broker or client processing the results.
Instead, a pipeline extension is used to process and report the pipeline output.

Contact [support@sighthound.com](mailto:support@sighthound.com) with any questions, and visit our [Developer Portal](https://dev.sighthound.com) for more information.


## General

Before getting started, you must copy your `sighthound-license.json` into the `./StandaloneSIOWithExtension/config/` folder. If you do not have a license, please contact [support@sighthound.com](mailto:support@sighthound.com).

## Running the folder watcher sample

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

## Running the RTSP sample

RTSP sample will consume the video feed via specified URL. The sample is packaged with a video file streamed from `live555` service container.
You can remove that service from `docker-compose-rtsp` if pointing the configuration in `config/analytics/pipelines-rtsp.json` to a different RTSP URL.

You start the sample in a manner similar to folder watcher sample, using `docker compose -f docker-compose-rtsp.yml up -d` command to start the service.

This configuration also demonstrates how to adapt the pipeline to a particular camera view. In this case, we see cars driving on the street,
cars making the right turn from the right lane and cars making the left turn from the left lane.
For the cars on the street we almost never see their license plates; thus it makes most sense to exclude those entirely. This is done by setting `lptSkipCarsWithoutLPs`
to `true`. The cars in the left lane may be seen or not, depending on whether there are cars in the right lane to occlude them. We expect that no one would want a
camera deployed in such non-deterministic way - thus assuming that monitoring the right turn lane is the purpose of this camera. Setting filters in `boxFilter-rtsp.json`
ensures we're not going to analyze objects outside of the bottom right quadrant ROI (`lp_roiFilter` accomplishes that), and won't analyze objects below size threshold (`vehicle_SizeFilter`
and `lp_SizeFilter` filters accomplish that).


## OS Compatibility

`SIO_DOCKER_TAG_VARIANT` environment variable used in `docker-compose` controls the flavor of SIO analytics container image. While on x86 systems thing largely work without setting it, on Jetson-based system, set it to the value most compatible with your base OS.

* `-r32.4.3-arm64v8` (built for hardware running Jetpack 4.4)
* `-r32.7.3-arm64v8` (built for hardware running Jetpack 4.6)
* `-r35.3.1-arm64v8` (work in progress, built for hardware running Jetpack 5.1)
* `-amd64` for x86 based systems

