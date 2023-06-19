#!/bin/bash

cd `dirname $0`
docker-compose -f docker-compose.interactive.yml run --rm sio


