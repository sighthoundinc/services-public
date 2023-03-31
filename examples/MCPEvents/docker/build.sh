#!/bin/bash
pushd $(dirname $0)/../
docker build -t mcpevents -f docker/Dockerfile ../
