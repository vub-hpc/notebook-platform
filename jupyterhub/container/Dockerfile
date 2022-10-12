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
# JupyterHub 2.0 + OAuthenticator + BatchSpawner
# based on https://github.com/jupyterhub/oauthenticator/blob/main/examples/full/Dockerfile
# meant to be run rootless

FROM jupyterhub/jupyterhub:2.0

MAINTAINER VUB-HPC <hpc@vub.be>

### System tools
RUN apt update
# install SSH client for BatchSpawner
RUN apt install -y --no-install-recommends openssh-client
# install sudo for BatchSpawner
RUN apt install -y sudo
# make /bin/sh symlink to bash instead of dash
RUN echo "dash dash/sh boolean false" | debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash

### Operator non-root user and extra groups
COPY sudoers.conf /etc/sudoers
RUN groupadd --gid 2000 etcconf  # special access to config files in bind folders
RUN groupadd --gid 2001 clients  # can be impersonated with sudo
RUN useradd --shell /bin/bash --create-home --groups etcconf jupyterhub
# switch to non-root operator
USER jupyterhub
WORKDIR /home/jupyterhub

### Jupyter Hub extras
ENV PATH "/home/jupyterhub/.local/bin:$PATH"

# install oauthenticator 
RUN python3 -m pip install --user oauthenticator
RUN mkdir oauthenticator
RUN chmod 700 oauthenticator

ENV OAUTHENTICATOR_DIR "/home/jupyterhub/oauthenticator"
ENV OAUTH2_AUTHORIZE_URL "https://account.vscentrum.be/django/oauth/authorize/"
ENV OAUTH2_TOKEN_URL "https://account.vscentrum.be/django/oauth/token/"
ENV OAUTH2_USERDATA_URL "https://account.vscentrum.be/django/oauth/current_vsc_user/"
ENV OAUTH2_USERNAME_KEY "id"

# install BatchSpawner
RUN python3 -m pip install --user batchspawner

# install vsc-config (local sources)
RUN python3 -m pip install --user vsc-base
COPY vsc-config-master.tar.gz /usr/local/src/ 
RUN python3 -m pip install --user /usr/local/src/vsc-config-master.tar.gz

# adduser wrapper
RUN echo -e '#!/bin/sh\nsudo useradd $@' > .local/bin/useradd
RUN chmod 750 .local/bin/useradd

