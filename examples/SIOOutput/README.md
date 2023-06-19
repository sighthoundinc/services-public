# SIO Output Example

This example prints SIO Data to console.

## Quickstart

```bash
docker-compose up
```

## Example output

```bash
example-sio-output  | AMQP configuration: {'host': 'rabbitmq', 'port': '5672', 'exchange': 'anypipe', 'routing_key': '#'}
example-sio-output  | Starting AMQP Listener on rabbitmq:5672
example-sio-output  | Message from source: my-video frame: my-video-frame-375882-1678216997580 at 2023-03-08 18:27:45
example-sio-output  |  With objects:
example-sio-output  |   - vehicles:car (my-video-car-59060-1678216997595)  at (1136,315)
example-sio-output  |  With media events:
example-sio-output  |   - image (59061)
example-sio-output  | ---------------
example-sio-output  | 
example-sio-output  | Message from source: my-video frame: my-video-frame-375883-1678216997580 at 2023-03-08 18:27:45
example-sio-output  |  With objects:
example-sio-output  |   - vehicles:car (my-video-car-59061-1678216997595)  at (1023,300)
example-sio-output  |  With media events:
example-sio-output  |   - image (59062)
example-sio-output  | ---------------
example-sio-output  | 
example-sio-output  | Message from source: my-video frame: my-video-frame-375884-1678216997580 at 2023-03-08 18:27:45
example-sio-output  |  With objects:
example-sio-output  |   - vehicles:car (my-video-car-59062-1678216997595)  at (891,300)
example-sio-output  |  With media events:
example-sio-output  |   - image (59063)
```