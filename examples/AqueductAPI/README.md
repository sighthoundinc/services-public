# Aqueduct API

This is a Flask-based API to manage video analytics pipelines. The API provides functionalities to start, stop, delete, and fetch the status of pipelines.

## Features
- Start Pipeline: Initialize a new pipeline with specified parameters.
- Stop Pipeline: Terminate an existing pipeline.
- Delete Pipeline: Remove an existing pipeline.
- Fetch Status: Retrieve the status of all pipelines or a single pipeline.

## How to run
First start all the dependencies:
```bash
./scripts sh-services apply ./examples/AqueductAPI/aqueduct.conf
cd ./examples/AqueductAPI
```

And then build and run the Docker Compose:
```bash
docker compose build
docker compose up
```

Your API should now be accessible at http://localhost:8888.

## API Endpoints
- POST `/pipelines/start`: Starts a new pipeline.
- POST `/pipelines/stop`: Stops an existing pipeline.
- POST `/pipelines/delete`: Deletes an existing pipeline.
- GET `/pipelines/status`: Gets the status of all pipelines.
- GET `/pipelines/status/<string:sourceId>`: Gets the status of a specific pipeline.
- GET `/health`: Health check.
