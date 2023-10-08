# SIO service Manual
short description: SIO is the Sighthound Computer Vision Engine

## Instructions

Choose one of the following operation modes

### Camera (default)
Just run:
```
../scripts/sh-services up sio
# or docker compose up -d
```

### Live555 mode

Run the following commands:
```
cp examples/live555/* conf
../scripts/sh-services merge sio
../scripts/sh-services up sio
```
#### UI compatibility
The UI uses a legacy merge tool and for that reason, configurations need to go in `custom.env`
The new merge tool does support `*.env` filenames ordered by alphabetically.
RUn:
```
cp examples/live555/0099-example.env conf/custom.env
```

### Plugins mode

Run the following commands:
```
cp examples/plugins/* conf
../scripts/sh-services merge sio
../scripts/sh-services up sio
```

