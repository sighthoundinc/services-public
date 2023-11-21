# Aqueduct UI

This example depends completely on the other example [Aqueduct UI](../AqueductAPI/)

## Quickstart

First of all we need to set SIO in Aqueduct mode.
Do that by running:

```bash
./scripts/sh-services apply ./examples/AqueductAPI/aqueduct.conf
```

This command will ask for a video to use as a fake RTSP, just select one MKV file, and the rest is automatic.

After the setup, start the Aqueduct API in the background:

```bash
./scripts/sh-services start_example AqueductAPI 
```

And check the logs:

```bash
docker logs aqueductapi-aqueduct-api-1 
```

And finally, start the Aqueduct UI:

```bash
./scripts/sh-services start_example AqueductUI 
```

And open the website at: http://localhost:4173