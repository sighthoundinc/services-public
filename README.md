# Sighthound Services

This repository hosts a collection of services for the SIO (Sighthound.IO) ecosystem. Services are intended to run via the `./scripts/sh-services` script, which relies on Docker Compose. However, Docker Compose is not strictly necessary for configuring or using this repository.

![System architecture](docs/media/architecture.png)

The included services are as follows:

- **SIO**: The computer vision analytics engine.
- **MCP**: Media manager service, which includes:
  - A REST API
  - Automatic Storage cleanup routines  
  **Important**: MCP relies on sharing media store folders with the SIO service, and listens on the AMQP message bus for media creation events (e.g., new video recordings or event-driven JPEG images). It then provides the API to access that media (see [http://localhost:9097](http://localhost:9097) for documentation) and controls its lifecycle (i.e., automatic cleanup).  
  **If you disable MCP while SIO is still generating media, SIO’s output will not be cleaned up, causing storage usage to grow indefinitely**.
- **RabbitMQ**: Default AMQP broker and messaging platform.
- **Live555**: An RTSP server for testing purposes. *Disabled by default.*
- **AMQP Stats**: Connects to RabbitMQ and displays SIO output data. *Disabled by default.*

This repository can serve either as a **turnkey deployment model** or as a guide for creating customer-specific application deployments using **SIO** and **MCP**. For illustration of some sample uses, please refer to the `examples` folder.

The `./scripts/sh-services` script is a basic tool that triggers `docker-compose up/down` commands as needed (see [scripts/README.md](scripts/README.md) for more details). However, the primary logic lies in *configuration management*. This Command-Line Interface (CLI) tool reads the `conf` folder for each service and merges the configurations, based on alphanumeric priority, into the `.env` file used by Docker Compose.

---

## Turnkey Scenario

In a turnkey scenario, each service is managed with:
- An individual `docker-compose` configuration file
- An optional (or auto-generated) `.env` file containing relevant environment variables
- A collection of service-specific configuration files in a `conf` subfolder

To help orchestrate these services (with disjointed `docker-compose` and environment configuration), the `sh-services` CLI utility was introduced.

![Folder Structure](docs/media/folders.png)

### Configuration Priority:

If you have multiple configuration files such as:

- `default.env`
- `0009-customer.env`
- `0001-system.env`

the order of priority (highest to lowest) is based on the filename in ascending *alphanumeric* order:
1. `0001-system.env`
2. `0009-customer.env`
3. `default.env`

The file processed *earliest* has the highest priority, meaning it **overwrites** any conflicting settings in the files processed later.

---

## Quick Start

This guide will help you set up SIO to point to a fake RTSP generated by Live555 and start processing video.

![live555](docs/media/live555.png)

### Prerequisites (for non-dnncam devices)

On Sighthound DNNCam devices, services come preinstalled, and the device GUI interacts with them. If you are using a DNNCam, we suggest relying on the GUI to configure/update services (though it is not strictly required). On other devices, you need to:

1. **Install Sighthound Services**  
2. **Install license and key files**  
3. **Log in to the Docker registry**  

#### 1. Installing Sighthound Services

Set up a base directory for Sighthound:

```bash
SH_BASE="/data/sighthound"
mkdir -p "${SH_BASE}"
cd "${SH_BASE}"
```

Next, retrieve the Sighthound Services either by cloning this repo or extracting the latest release.

**Option 1: Clone the repo**:

```bash
git clone git@github.com:sighthoundinc/services.git
cd services
# Optionally: checkout the latest release
RELEASE="v1.4.1"
git checkout tags/${RELEASE}
```

**Option 2: Download and extract the latest release**:

```bash
RELEASE="v1.3.0"
mkdir "${SH_BASE}"/services
cd "${SH_BASE}"/services
wget https://github.com/sighthoundinc/services/releases/download/${RELEASE}/sh-services-${RELEASE}.tar.gz
tar -xvf sh-services-${RELEASE}.tar.gz
rm sh-services-${RELEASE}.tar.gz
```

#### 2. Installing SIO analytics license and Docker registry key

Copy (or secure copy) the Sighthound-provided files to the correct location:

```bash
# License
mkdir -p "${SH_BASE}"/license
cp ~/Downloads/sighthound-license.json "${SH_BASE}"/license

# Docker key
mkdir -p "${SH_BASE}"/keys
cp ~/Downloads/sighthound-keyfile.json "${SH_BASE}"/keys
```

Alternatively just run:

```bash
./scripts/sh-services license
```

#### 3. Logging into the Docker Registry

```bash
docker login -u _json_key -p  "$(cat "${SH_BASE}"/keys/sighthound-keyfile.json)" us-central1-docker.pkg.dev
```

---

### Enabling a test RTSP (Live555)

If you need to test SIO analytics service and do not have an available RTSP source, you can enable the Live555 service:

```bash
./scripts/sh-services enable live555
```

Next, copy your test video file to the Live555 mount path:

```bash
mkdir -p "${SH_BASE}"/media/input/video/live555
# cp or scp your test video
cp <my-video> "${SH_BASE}"/media/input/video/live555/my-video.mp4
```

You can also do this via the helper script:

```bash
./scripts/sh-services select_live555_video
# Enter the path of your MKV/MP4 file when prompted
```

Finally, enable the Live555 SIO configuration:

```bash
./scripts/sh-services select_example sio file-rtsp
```

---

### Configure SIO

**Requirement**: `jq` must be installed (if you plan on using the interactive config scripts).

```bash
./scripts/sh-services config sio
```

---

### Running Sighthound Services

First, check the license:

```bash
./scripts/sh-services up license
```

Then start all services:

```bash
./scripts/sh-services up all
```

To modify the configuration of any service, run:

```bash
./scripts/sh-services edit all
```

---

### Testing the Setup Visually

To visually confirm your setup, use the `SIO_RTSP_Output` example to create an RTSP feed of your Live555 video annotated with the analytics data:

```bash
cd ./examples/SIO_RTSP_Output
docker compose up
```

Then open VLC at `rtsp://localhost:8554/live`.

This should be sufficient for most users to get started with the Sighthound Services. For more detailed information on individual services, how to change Docker environment variables, and deployment instructions, please see the full documentation below.

---

## Services in Detail

Below is additional information about each individual service, including their role, exposed ports, and any special usage instructions.

### **MCP (Media Control Point)**

**MCP** is a service that listens for output from the SIO analytics container and provides indexing, time-based access, and cleanup of any media generated by SIO.

- **Key Function**: MCP automatically cleans up stored images and videos (e.g., older recordings), preventing storage from filling up.
- **Exposed port**: `9097` (the MCP REST API)

#### **Important Warning About Disabling MCP**

If you **disable MCP** while SIO is still configured to record images or video, you will **lose the automatic cleanup feature**. This means media files (recorded video segments, snapshots, etc.) will remain on disk indefinitely, potentially filling up your hard disk. 

If you do not want any media to be recorded by SIO, you must disable it on the **SIO side** (see the [Disabling SIO Recording](#disabling-sio-recording) section below). Otherwise, ensure you have **another mechanism** for cleaning up your media.

### **sio (Sighthound IO Analytics)**

- **Role**: The analytics engine processing live video feeds (or images) and emitting analytics on the AMQP bus.
- **Media Generation**: SIO can store images or videos for each configured camera source if `recordTo` or `imageSaveDir` are specified in the SIO pipeline JSON.
- **If MCP is disabled** and SIO is still generating media, you must provide your own cleanup mechanism or **disable SIO’s recording feature**.

### **rabbitmq (AMQP broker)**

- **Exposed ports**:
  - `5672` (RabbitMQ default)
  - `15672` (RabbitMQ Management console)

### **live555 (RTSP Test Server)**

A simple RTSP server for testing. **Disabled by default**.

### **amqp-stats**

A small utility that connects to RabbitMQ and displays SIO output data. **Disabled by default**.

---

## Configuration

1. Set a base path variable:
   ```bash
   SH_BASE="/data/sighthound"
   ```
2. Create directories:
   ```bash
   mkdir -p "${SH_BASE}"
   mkdir -p "${SH_BASE}"/media
   mkdir -p "${SH_BASE}"/services
   mkdir -p "${SH_BASE}"/license
   ```
3. Install the SIO license at `"${SH_BASE}"/license/sighthound-license.json`.
4. Uncompress the services tarball into `"${SH_BASE}"/services`.
5. Modify the SIO configuration (JSON) in `sio/conf/sio.json` or whichever file you use, specifying the RTSP URL, pipeline parameters, etc.
6. Create the Docker `.env` files by running:
   ```bash
   ./scripts/sh-services merge all
   ```

---

## SIO Pipeline Parameters

SIO configuration is typically provided in `./sio/conf/sio.json` (or a similarly named file for each pipeline). This JSON specifies:
- One or more pipelines or streams
- Parameters that control how each pipeline behaves (e.g., analytics type, input source, media recording)

Common parameters:

- `VIDEO_IN`: The RTSP URL to use
- `fpsLimit`: Limits the FPS intake by the analytics pipeline
- `recordTo`: Path for video storage. For example: `/data/sighthound/media/output/video/${sourceId}/`
- `imageSaveDir`: Path for image storage. For example: `/data/sighthound/media/output/image/${sourceId}/`

**If you do not want to store any media files (images or videos), set `recordTo` and `imageSaveDir` to empty strings** (see [Disabling SIO Recording](#disabling-sio-recording)).

For more advanced options, consult:
- [VehicleAnalytics Documentation](https://dev.sighthound.com/sio/pipelines/VehicleAnalytics/)
- [TrafficAnalytics Documentation](https://dev.sighthound.com/sio/pipelines/TrafficAnalytics/)

---

## Changing Docker Environment Variables

The `.env` [file](https://docs.docker.com/compose/environment-variables/set-environment-variables/#substitute-with-an-env-file) is generated by `sh-services` at runtime. To modify the environment via CLI, either:

1. Run:
   ```bash
   ./scripts/sh-services edit <service>
   ```
   and follow the prompts to edit `.env` variables interactively.
2. Add a user-specific file with an `.env` extension to the `conf/` folder, e.g. `sio/conf/0009-debug.env`:
   ```bash
   echo "MY_VARIABLE=24" > sio/conf/0009-debug.env
   echo "SIO_DOCKER_TAG=r250201" >> sio/conf/0009-debug.env

   ./scripts/sh-services merge sio
   ```

---

## Modifying the SIO Release Version

To change the SIO Docker image version/tag:

1. Run `./scripts/sh-services edit sio`.
2. Select `Edit service (.env)`.
3. Find the variable `SIO_DOCKER_TAG`.
4. Set it to your desired version.
5. Save the file.

A file named `sio/conf/0001-edit.env` will be created, overriding the `default.env` or any lower-priority files.

---

## Deployment

To deploy all enabled services:

```bash
./scripts/sh-services up all
```

Visit:

- [http://localhost:15672](http://localhost:15672) for the RabbitMQ management console
- [http://localhost:9097](http://localhost:9097) for MCP’s REST API

---

## Disabling a Service

You can disable a service in two ways:

```bash
./scripts/sh-services disable <service>
# OR
touch <service>/disabled
```

Once disabled, `docker-compose` will not spin up that service.

### **Warning**: Disabling MCP

If you disable MCP while SIO is still generating media, you **will not** have automatic cleanup of videos/images. You **must** either handle cleanup yourself or disable SIO’s media generation. Otherwise, your disk **will fill up** over time.

---

## Disabling SIO Recording

**If you want to ensure no images or videos are generated by SIO**, you can remove or clear out the `recordTo` and `imageSaveDir` parameters for your pipelines. For instance, an example minimal SIO pipeline JSON might look like:

```json
{
    "your_stream": {
        "parameters": {
            "VIDEO_IN": "rtsp://192.168.1.10:554/yourcamera",
            "recordTo": "",
            "imageSaveDir": ""
        }
    }
}
```

By leaving `recordTo` and `imageSaveDir` as empty strings, **no media files** are saved to disk. This effectively prevents your storage from growing due to video/image recordings.

> **Example**: You can find a similar configuration in `services/sio/examples/count-sensor-nomedia/sio.json`.

---

## Examples

For development examples and demonstration scripts, see the [docs/examples](docs/examples) folder.

---

## Tips and Tricks

- To use `sh-services` more conveniently, you can add its script path to your `$PATH`:
  ```bash
  export PATH=${PATH}:"${SH_BASE}"/services/scripts
  ```
  Then you can call:
  ```bash
  sh-services up all
  ```

- Re-enable a disabled service:
  ```bash
  ./scripts/sh-services enable <service>
  # OR
  rm <service>/disabled
  ```

This guide should help you get started with Sighthound Services and allow you to efficiently use, manage, and deploy these services. If any part of the guide needs clarification, or if you encounter any issues while using the services, please let us know so we can improve the documentation and address the problem.