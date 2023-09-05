# Sighthound Scripts Manual

## SH-Services

This script is a bash script that provides a set of commands to manage docker-compose services. The script is called sh-services and is executed by running ./scripts/sh-services. The following is a list of the available commands:

### Apply 
Usage: `./scripts/sh-services apply <file>`
Applies a configuration file, this is useful for setting up the environment for an specific usecase.
For example, for Open telemetry you could run: `./scripts/sh-services apply examples/OpenTelemetry/opentelemetry.conf`
and that would set the live555 video, setup sio, mcp, rabbitmq, and start those services, all in one command.
See: [opentelemetry.conf](../examples/OpenTelemetry/opentelemetry.conf)

### Merge
Usage: `./scripts/sh-services merge <file1> <file2> ...`

Combines several configuration files into a single .env file.

### Up
Usage: `./scripts/sh-services up <service(s)>`

Starts a docker-compose service.

### Down
Usage: `./scripts/sh-services down <service(s)>`

Stops a docker-compose service.

### Restart
Usage: `./scripts/sh-services restart <service(s)>`

Restarts a docker-compose service.

### Show
Usage: `./scripts/sh-services show <service(s)>`

Displays the .env configuration of a service.

### Status
Usage: `./scripts/sh-services status <service(s)>`

Shows the status of running services.

### Edit
Usage: `./scripts/sh-services edit <service(s)>`

Modifies configurations or settings of a service.

### Config
Usage: `./scripts/sh-services config <service(s)>`

Runs the configuration script of a service.
For example:
```
$ ./scripts/sh-services config sio
Summary of all sources:
one-person-one-car: rtsp://live555/test.mkv
1) Create a new source	    3) Exit
2) Edit an existing source
Select an option: ...
```

### Select Example
Usage: `./scripts/sh-services select_example <service> <>`

Selects an example configuration for a service. For example, you can run `./scripts/sh-services select_example sio aqueduct`.
And that would enable [this](../sio/examples/aqueduct) example.

### Enable
Usage: `./scripts/sh-services enable <service(s)>`

Turns on a service.

### Disable
Usage: `./scripts/sh-services disable <service(s)>`

Turns off a service.

### Depends
Usage: `./scripts/sh-services depends <service(s)>`

Shows the dependencies of a service and its status.

### License
Usage: `./scripts/sh-services license`

Checks or creates the license file.

### Clean Media
Usage: `./scripts/sh-services clean_media`

Removes all media files and databases.

### Clean Logs
Usage: ./scripts/sh-services clean_logs

Empties the log files without deleting them.

### Remove Orphans
Usage: `./scripts/sh-services remove_orphans`

Removes containers for services not defined in the current configuration.

### PS
Usage: `./scripts/sh-services ps`

Lists services and their status.

## Usage

You can execute any of these commands by running the script with the command as its first argument. For example, to start a service, you can run:

```bash
./scripts/sh-services up my-service
```