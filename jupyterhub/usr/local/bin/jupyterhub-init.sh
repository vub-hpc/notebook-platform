#!/bin/bash
#
# Copyright 2022 Vrije Universiteit Brussel
#
# This file is part of notebook-platform,
# originally created by the HPC team of Vrij Universiteit Brussel (http://hpc.vub.be),
# with support of Vrije Universiteit Brussel (http://www.vub.be),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# the Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/vub-hpc/notebook-platform
#
# notebook-platform is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License v3 as published by
# the Free Software Foundation.
#
# notebook-platform is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
###
#
# Start existing container for JupyterHub
# If container is missing, create and start a new one
#
# This init script is meant to be run from within a systemd service
# Containers are started in the background (detached mode)
# Service is attached to `conmon`, the monitoring tool of podman
#
# arguments:
#   1: name of container
#
# optional environment variables:
#   JH_CONTAINER_RUNDIR: path to runtime directory
#

JH_CONTAINER_NAME=${1:-jupyterhub}
JH_CONTAINER_TAG="2.0"
JH_CONTAINER_SRC="localhost/jupyterhub-rootless:$JH_CONTAINER_TAG"

# Custom runtime directory
pid_file=""
cid_file=""
if [ -n "$JH_CONTAINER_RUNDIR" ]; then
    pid_file="$JH_CONTAINER_RUNDIR/$JH_CONTAINER_NAME.pid"
    podman_pid="--conmon-pidfile $pid_file"
    cid_file="$JH_CONTAINER_RUNDIR/$JH_CONTAINER_NAME.cid"
    podman_cid="--cidfile $cid_file"
fi

# Container port
# Forward container port 8000 (web) and port 8081 (api)
podman_port_web="-p 8000:8000/tcp"
podman_port_api="-p 8081:8081/tcp"
podman_port="$podman_port_web $podman_port_api"

# VSC user home directories
vsc_institutes="brussel"
vsc_home_mounts=""
for institute in $vsc_institutes; do
    vsc_home_mounts="$vsc_home_mounts -v /user/$institute:/user/$institute"
done

# Run JupyterHub container
if podman container exists $JH_CONTAINER_NAME; then
    # Start existing container
    podman_cmd="start $JH_CONTAINER_NAME"
else
    # Cleanup old runtime files
    [ -f $pid_file ] && /bin/rm -f $pid_file
    [ -f $cid_file ] && /bin/rm -f $cid_file

    # Create container and run it
    podman_run_args=(
        -d                                  # run in detached mode
        $podman_pid $podman_cid             # define runtime files
        $podman_port                        # define container network settings
        $vsc_home_mounts                    # bind mount VSC_HOME directories
        --log-driver=journald               # use journald to manage container logs
        -v /dev/log:/dev/log                # bind mount /dev/log to make container logs available in host
        -v /etc/pki:/etc/pki                # bind directory with certificates
        -v /etc/jupyterhub:/etc/jupyterhub  # bind directory with configuration files
        --group-add=etcconf                 # add secondary groups from host system
        --name=$JH_CONTAINER_NAME           # define container name
        $JH_CONTAINER_SRC                   # source of container image
        jupyterhub                               # COMMAND #
        -f /etc/jupyterhub/jupyterhub_config.py  # configuration file
    )
    podman_cmd="run ${podman_run_args[@]}"
fi

echo "Launching container: /usr/bin/podman $podman_cmd"
exec /usr/bin/podman $podman_cmd
