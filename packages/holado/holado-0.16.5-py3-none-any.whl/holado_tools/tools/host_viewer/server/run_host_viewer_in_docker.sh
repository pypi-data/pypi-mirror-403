#!/bin/bash

# Script to launch Host Viewer as a docker image.
# 
# Host Viewer exposes a REST API with host services.
# It is accessible on localhost, and also on a docker network if HOLADO_NETWORK is defined.
# API is accessible on port HOLADO_HOST_VIEWER_HOSTPORT from localhost and port HOLADO_HOST_VIEWER_PORT from network.
#
# REST API specification is in file rest/openapi.yaml.
#
# REQUIREMENTS:
#     Have access to any HolAdo registry.
#
#     Optionally, define in .profile the following variables
#         - HOLADO_HOST_VIEWER_HOST: host name or name of the container
#         - HOLADO_HOST_VIEWER_HOSTPORT: REST API port to use from localhost (default: 51231)
#         - HOLADO_HOST_VIEWER_PORT: REST API port to use from network HOLADO_NETWORK (default: 51231)
#         - HOLADO_IMAGE_REGISTRY: docker image registry to use (default: holado/host_viewer)
#         - HOLADO_IMAGE_TAG: docker image tag to use (default: latest)
#         - HOLADO_OUTPUT_BASEDIR: absolute path to base output directory (default: [HOME]/.holado/output)
#         - HOLADO_USE_LOCALHOST: force the container network to 'host'.
#         - HOLADO_NETWORK: specify on which network the docker is run.
#


WORK_DIR="$(pwd)"

if [[ -z "$HOLADO_IMAGE_REGISTRY" ]]; then
    HOLADO_IMAGE_REGISTRY=holado/host_viewer
fi
if [[ -z "$HOLADO_IMAGE_TAG" ]]; then
    HOLADO_IMAGE_TAG=latest
fi
VIEWER_IMAGE=${HOLADO_IMAGE_REGISTRY}:${HOLADO_IMAGE_TAG}

# Update docker image
echo "Updating docker image ${VIEWER_IMAGE}..."
docker pull ${VIEWER_IMAGE}

# Define output directory
if [[ ! -z "$HOLADO_OUTPUT_BASEDIR" ]]; then
    OUTPUT_DIR=${HOLADO_OUTPUT_BASEDIR}
else
    OUTPUT_DIR=${HOME}/.holado/output
fi
echo "Output directory: $OUTPUT_DIR"

# Define resources directory
if [[ ! -z "$HOLADO_LOCAL_RESOURCES_BASEDIR" ]]; then
    RESOURCES_DIR=${HOLADO_LOCAL_RESOURCES_BASEDIR}
else
    RESOURCES_DIR=${HOME}/.holado/resources
fi
echo "Resources directory: $RESOURCES_DIR"

# Make dirs
if [ ! -d ${OUTPUT_DIR} ]; then
    echo "Create output directory: ${OUTPUT_DIR}"
    mkdir -p ${OUTPUT_DIR}
fi
if [ ! -d ${RESOURCES_DIR} ]; then
    echo "Create resources directory: ${RESOURCES_DIR}"
    mkdir -p ${RESOURCES_DIR}
fi

# Define container network
if [ "$HOLADO_USE_LOCALHOST" = True ]; then
	NETWORK_DEF_COMMAND="--network=host"
else
	if [[ ! -z "$HOLADO_NETWORK" ]]; then
		NETWORK_DEF_COMMAND="--network $HOLADO_NETWORK"
	else
		NETWORK_DEF_COMMAND=""
	fi
fi

# Define ports to use
if [[ -z "$HOLADO_HOST_VIEWER_HOSTPORT" ]]; then
    HOLADO_HOST_VIEWER_HOSTPORT=51233
fi
if [[ -z "$HOLADO_HOST_VIEWER_PORT" ]]; then
    HOLADO_HOST_VIEWER_PORT=51233
fi

# Docker run 
if [[ -z "$HOLADO_HOST_VIEWER_NAME" ]]; then
    HOLADO_HOST_VIEWER_NAME=holado_host_viewer
fi

echo
echo "Running Host Viewer..."
echo "    container name: ${HOLADO_HOST_VIEWER_HOST}"
echo "    host port: ${HOLADO_HOST_VIEWER_HOSTPORT}"
echo "    port: ${HOLADO_HOST_VIEWER_PORT}"
#echo "    NETWORK_DEF_COMMAND=${NETWORK_DEF_COMMAND}"
echo
docker run --rm --user root --name ${HOLADO_HOST_VIEWER_NAME} \
    --privileged -v $(docker info --format '{{.SecurityOptions}}' | grep -q rootless && echo -n "/run/user/$(id -u ${USER})/docker.sock" || echo -n "/var/run/docker.sock"):/var/run/docker.sock \
    -v "${OUTPUT_DIR}":/output \
    -v "${RESOURCES_DIR}":/resources \
    -e HOLADO_OUTPUT_BASEDIR=/output \
    -e HOLADO_LOCAL_RESOURCES_BASEDIR=/resources \
    -e HOLADO_HOST_VIEWER_PORT=${HOLADO_HOST_VIEWER_PORT} \
    ${NETWORK_DEF_COMMAND} \
    -p ${HOLADO_HOST_VIEWER_HOSTPORT}:${HOLADO_HOST_VIEWER_PORT} \
    ${VIEWER_IMAGE}

