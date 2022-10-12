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
# Configuration file for JupyterHub integrated into VUB-HPC clusters
# - Authentication with VSC account page (OAuthenticator)
# - Notebook spawend in remote Slurm cluster (BatchSpawner)
#
#------------------------------------------------------------------------------
# Network configuration
#------------------------------------------------------------------------------
# Listen on all interfaces
# proxy is in localhost, users are external and spawners are internal
c.JupyterHub.bind_url = 'https://0.0.0.0:8000'
c.JupyterHub.hub_ip = '0.0.0.0'
# IP address or hostname that spawners should use to connect to the Hub API
c.JupyterHub.hub_connect_ip = 'host.internal.domain'

#------------------------------------------------------------------------------
# VSC user creation in the system
# - create local VSC users on-the-fly with specicic UID and home directories
#------------------------------------------------------------------------------
from vsc.config.base import HOME_KEY, VSC

def vsc_user_uid_home(username):
    """Create a new local VSC user on the system."""
    vsc = VSC()
    vsc_uid = vsc.user_uid_institute_map[username[:3]][0] + int(username[3:])
    vsc_user_institute = vsc.user_id_to_institute(vsc_uid)
    vsc_user_paths = vsc.user_pathnames(username, vsc_user_institute)
    vsc_home = vsc_user_paths[HOME_KEY]

    # UID in container corresponds to VSC number
    pod_id = username[3:]

    # define command to add VSC user to system
    add_user_cmd = ['useradd', '--shell', '/bin/bash']
    # add VSC user details to adduser cmd
    add_user_cmd += ['--uid', pod_id, '--user-group']
    add_user_cmd += ['--no-create-home', '--home-dir', vsc_home]
    # add VSC user to JupyterHub client group (controls sudo permissions)
    add_user_cmd += ['--groups', 'clients']

    return add_user_cmd

#------------------------------------------------------------------------------
# OAuthenticator configuration
# - use GenericOAuthenticator with the VSC account page
# - create local VSC users on-the-fly in the JupyterHub container
# - enable SSL
#------------------------------------------------------------------------------
# VSC users have to be created with specific UID and home directories
from oauthenticator.generic import LocalGenericOAuthenticator

class VSCGenericOAuthenticator(LocalGenericOAuthenticator):
    def add_system_user(self, user):
        """Inject VSC user ID and home directory into adduser command"""
        self.add_user_cmd = vsc_user_uid_home(user.name)
        super(VSCGenericOAuthenticator, self).add_system_user(user)

# enable Oauth and automatically create logged users in the system
c.JupyterHub.authenticator_class = VSCGenericOAuthenticator
c.LocalAuthenticator.create_system_users = True

# Oauth application secrets in the VSC account page
c.GenericOAuthenticator.login_service = 'VSC Account'
c.GenericOAuthenticator.client_id = 'SECRET'
c.GenericOAuthenticator.client_secret = 'SECRET'
c.GenericOAuthenticator.oauth_callback_url = 'https://host.exernal.domain/hub/oauth_callback'
c.GenericOAuthenticator.scope = ['read']

# SSL certificates
c.JupyterHub.ssl_cert = '/etc/pki/tls/certs/host-ssl.crt'
c.JupyterHub.ssl_key = '/etc/pki/tls/private/host-ssl.key'

#------------------------------------------------------------------------------
# BatchSpawner configuration
# - use Slurm by connecting with SSH to a login node
# - define job script launching the notebook
#------------------------------------------------------------------------------
import batchspawner
c.JupyterHub.spawner_class = 'batchspawner.SlurmSpawner'
c.Spawner.http_timeout = 120

# default profile settings
c.BatchSpawnerBase.req_partition = 'ivybridge,skylake_mpi'
c.BatchSpawnerBase.req_runtime = '2:00:00'
c.BatchSpawnerBase.req_memory = '2G'
c.BatchSpawnerBase.req_nprocs = '1'

# job script needs to load batchspawner and JupyterLab or JupyterNotebook
c.BatchSpawnerBase.req_prologue = """
module load JupyterHub/2.0.2-GCCcore-10.3.0
"""

# execute all Slurm commands through SSH on the login node
c.SlurmSpawner.exec_prefix = "sudo -E -u {username} ssh "
# auto-accept keys from login node
c.SlurmSpawner.exec_prefix += "-o \'StrictHostKeyChecking no\' "
# login node hostname
c.SlurmSpawner.exec_prefix += "login.internal.domain "

# protect argument quoting in query command send through SSH
c.SlurmSpawner.batch_query_cmd = r"squeue -h -j {job_id} -o \'%T %B\'"

# pass the JupyterHub environment to sbatch through the SSH connnection
jh_env = ['JUPYTERHUB_API_TOKEN', 'JPY_API_TOKEN', 'JUPYTERHUB_CLIENT_ID', 'JUPYTERHUB_HOST', 'JUPYTERHUB_API_URL',
          'JUPYTERHUB_OAUTH_CALLBACK_URL', 'JUPYTERHUB_OAUTH_SCOPES', 'JUPYTERHUB_USER', 'JUPYTERHUB_SERVER_NAME',
          'JUPYTERHUB_ACTIVITY_URL', 'JUPYTERHUB_BASE_URL', 'JUPYTERHUB_SERVICE_PREFIX', 'JUPYTERHUB_SERVICE_URL']
# protect expansion of envars to be reused as input '${VAR@Q}'
jh_env = ' '.join([f'{var}=\"${{{var}@Q}}\"' for var in jh_env])
# protect envars from templating
jh_env = "{% raw %}env " + jh_env + "{% endraw %}"
# prepend the envars to the default sbatch command
c.SlurmSpawner.batch_submit_cmd = jh_env + " sbatch --parsable"

# the user server is launched with srun, ensure that it gets the job environment
c.SlurmSpawner.req_srun = 'srun --export=ALL'

# expand the execution hostname returned by sstat to a FQDN
c.SlurmSpawner.state_exechost_exp = r'\1.domain'

