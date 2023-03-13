# Copyright 2023 Vrije Universiteit Brussel
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
#------------------------------------------------------------------------------
# Network configuration
#------------------------------------------------------------------------------
# Listen on all interfaces
# proxy is in localhost, users are external and spawners are internal
c.JupyterHub.bind_url = 'https://0.0.0.0:8000'
c.JupyterHub.hub_ip = '0.0.0.0'
# IP address or hostname that spawners should use to connect to the Hub API
c.JupyterHub.hub_connect_ip = 'jupyterhub.internal.domain'

#------------------------------------------------------------------------------
# OAuthenticator configuration
# - use GenericOAuthenticator with the VSC account page
# - work without local VSC users in the JupyterHub container
# - enable SSL
#------------------------------------------------------------------------------
from oauthenticator.generic import GenericOAuthenticator
c.JupyterHub.authenticator_class = GenericOAuthenticator

# Oauth application secrets in the VSC account page
c.GenericOAuthenticator.login_service = 'VSC Account'
c.GenericOAuthenticator.client_id = 'SECRET'
c.GenericOAuthenticator.client_secret = 'SECRET'
c.GenericOAuthenticator.oauth_callback_url = 'https://notebooks.hpc.vub.be/hub/oauth_callback'
c.GenericOAuthenticator.scope = ['read']

# SSL certificates
c.JupyterHub.ssl_cert = '/home/jupyterhub/.ssl/jupyterhub.crt'
c.JupyterHub.ssl_key = '/home/jupyterhub/.ssl/jupyterhub.key'

#------------------------------------------------------------------------------
# Custom notebook spawner for VSC users
# - determine UID and home directory from VSC config
# - works without local VSC users
#------------------------------------------------------------------------------
from jupyterhub_moss import MOSlurmSpawner, set_config
from traitlets import default
from vsc.config.base import DATA_KEY, HOME_KEY, VSC

class VSCSlurmSpawner(MOSlurmSpawner):
    """
    Spawner that derives user environment from vsc-config to not rely on local users
    """
    vsc = VSC()

    def vsc_user_institute(self):
        "return institute of VSC user"
        vsc_uid = self.vsc.user_uid_institute_map[self.user.name[:3]][0] + int(self.user.name[3:])
        return self.vsc.user_id_to_institute(vsc_uid)

    @default("req_homedir")
    def vsc_homedir(self):
        "set default home directory to VSC_HOME"
        vsc_user_paths = self.vsc.user_pathnames(self.user.name, self.vsc_user_institute())
        return vsc_user_paths[HOME_KEY]

    @default("notebook_dir")
    def vsc_datadir(self):
        "set default notebook root directory to VSC_DATA"
        vsc_user_paths = self.vsc.user_pathnames(self.user.name, self.vsc_user_institute())
        return vsc_user_paths[DATA_KEY]

    def user_env(self, env):
        """get VSC user environment"""
        env["USER"] = self.user.name
        env["SHELL"] = "/bin/bash"
        env["HOME"] = self.req_homedir
        env["JUPYTERHUB_ROOT_DIR"] = self.notebook_dir
        return env

#------------------------------------------------------------------------------
# BatchSpawner configuration
# - use VSCSlurmSpawner
# - submit notebook job to Slurm by connecting with SSH to a login node
# - SSH connection stablished as JupyterHub operator
# - define job script parameters and commands launching the notebook
#------------------------------------------------------------------------------
set_config(c)
c.JupyterHub.spawner_class = VSCSlurmSpawner
c.Spawner.start_timeout = 600  # seconds from job submit to job start
c.Spawner.http_timeout = 120  # seconds from job start to reachable single-user server

# JupyterLab Environments in VUB
vub_lab_environments = {
    "2022_default": {
        # Text displayed for this environment select option
        "description": "2022a: Python v3.10.4 + kernels (default)",
        # Space separated list of modules to be loaded
        "modules": "JupyterHub/2.3.1-GCCcore-11.3.0",
        # Path to Python environment bin/ used to start jupyter on the Slurm nodes
        "path": "",
        # Toggle adding the environment to shell PATH (default: True)
        "add_to_path": False,
    },
    "2022_rstudio": {
        "description": "2022a: Python v3.10.4 + RStudio",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-11.3.0 "
            "jupyter-rsession-proxy/2.1.0-GCCcore-11.3.0 "
            "RStudio-Server/2022.07.2+576-foss-2022a-Java-11-R-4.2.1 "
            "IRkernel/1.3.2-foss-2022a-R-4.2.1 "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2022_matlab": {
        "description": "2022a: Python v3.10.4 + MATLAB",
        "modules": (
            "MATLAB/2022a-r5 "
            "JupyterHub/2.3.1-GCCcore-11.3.0 "
            "jupyter-matlab-proxy/0.5.0-GCCcore-11.3.0 "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2022_dask": {
        "description": "2022a: Python v3.10.4 + dask",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-11.3.0 "
            "dask-labextension/6.0.0-foss-2022a "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2022_nglview": {
        "description": "2022a: Python v3.10.4 + nglview",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-11.3.0 "
            "nglview/3.0.3-foss-2022a "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2021_default": {
        "description": "2021a: Python v3.9.5 + kernels (default)",
        "modules": "JupyterHub/2.3.1-GCCcore-10.3.0",
        "path": "",
        "add_to_path": False,
    },
    "2021_rstudio": {
        "description": "2021a: Python v3.9.5 + RStudio",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-10.3.0 "
            "jupyter-rsession-proxy/2.1.0-GCCcore-10.3.0 "
            "RStudio-Server/1.4.1717-foss-2021a-Java-11-R-4.1.0 "
            "IRkernel/1.2-foss-2021a-R-4.1.0 "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2021_matlab": {
        "description": "2021a: Python v3.9.5 + MATLAB",
        "modules": (
            "MATLAB/2021a "
            "JupyterHub/2.3.1-GCCcore-10.3.0 "
            "jupyter-matlab-proxy/0.3.4-GCCcore-10.3.0 "
            "MATLAB-Kernel/0.17.1-GCCcore-10.3.0 "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2021_dask": {
        "description": "2021a: Python v3.9.5 + dask",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-10.3.0 "
            "dask-labextension/5.3.1-foss-2021a "
        ),
        "path": "",
        "add_to_path": False,
    },
    "2021_nglview": {
        "description": "2021a: Python v3.9.5 + nglview",
        "modules": (
            "JupyterHub/2.3.1-GCCcore-10.3.0 "
            "nglview/3.0.3-foss-2021a "
        ),
        "path": "",
        "add_to_path": False,
    },
}

# Partition descriptions
vub_partitions_hydra = {
    "broadwell": {                         # Partition name
        "architecture": "x86_86",          # Nodes architecture
        "description": "Intel Broadwell",  # Displayed description
        "max_runtime": 12*3600,            # Maximum time limit in seconds (Must be at least 1hour)
        "simple": True,                    # True to show in Simple tab
        "jupyter_environments": vub_lab_environments,
    },
    "skylake": {
        "architecture": "x86_86",
        "description": "Intel Skylake",
        "max_runtime": 12*3600,
        "simple": True,
        "jupyter_environments": vub_lab_environments,
    },
    "pascal_gpu": {
        "architecture": "CUDA",
        "description": "Nvidia Pascal P100",
        "max_runtime": 6*3600,
        "simple": True,
        "jupyter_environments": vub_lab_environments,
    },
    "skylake_mpi": {
        "architecture": "x86_86",
        "description": "Intel Skylake with InfiniBand",
        "max_runtime": 6*3600,
        "simple": False,
        "jupyter_environments": vub_lab_environments,
    },
}

vub_partitions_manticore = {
    "ivybridge": {
        "architecture": "x86_86",
        "description": "Intel Ivybridge",
        "max_runtime": 8*3600,
        "simple": True,
        "jupyter_environments": vub_lab_environments,
    },
    "ampere_gpu": {
        "architecture": "CUDA",
        "description": "Nvidia Ampere",
        "max_runtime": 8*3600,
        "simple": True,
        "jupyter_environments": vub_lab_environments,
    },
    "skylake_mpi": {
        "architecture": "x86_86",
        "description": "Intel Skylake with InfiniBand",
        "max_runtime": 4*3600,
        "simple": False,
        "jupyter_environments": vub_lab_environments,
    },
}

c.MOSlurmSpawner.partitions = vub_partitions_hydra

# Single-user server job loads its own JupyterHub with batchspawner (for comms)
# plus either JupyterLab or JupyterNotebook
# Job environment is reset to an aseptic state avoiding user's customizations
c.BatchSpawnerBase.req_prologue = """
function serialize_env(){
    # Pick all environment variables matching each given pattern and
    # output their definitions ready to be exported to the environment
    for var_pattern in $@; do
        var_pattern="^${var_pattern}="
        while read envar; do
            # Protect contents of variables with printf %q because this job
            # script is sent as standard input to sbatch through ssh and sudo
            envar_name=${envar/=*}
            printf "export %q=%q\n" "${envar_name}" "${!envar_name}"
        done < <(env | grep "$var_pattern" )
    done
}

# Launch notebook in aseptic environment
# note: the initial shell of the job script will evaluate the whole `exec env -i bash`
# command before its execution. This means that any variable ${} or command substitution $()
# in the input will be carried out before entering the minimal environment of `env -i`.
exec env -i bash --norc --noprofile <<EOF
$(serialize_env HOME SHELL TMPDIR SLURM.* UCX_TLS JUPYTER.* JPY_API_TOKEN)
source /etc/profile
source /etc/bashrc
"""
c.BatchSpawnerBase.req_epilogue = """
EOF
"""

# Execute all Slurm commands on the login node
# jump to login node as JupyterHub user with SSH and the following settings (~/.ssh/config):
# - disable StrictHostKeyChecking to auto-accept keys from login nodes
# - pass full JupyterHub environment with SendEnv
c.SlurmSpawner.exec_prefix = "ssh login.internal.domain "
# slurm cluster settings
c.SlurmSpawner.exec_prefix += "SLURM_CLUSTERS=hydra SLURM_CONF=/etc/slurm/slurm.conf "
# switch to end-user in the login node
c.SlurmSpawner.exec_prefix += "sudo -u {username} "

# fix templating for scancel
c.SlurmSpawner.batch_cancel_cmd = "scancel {{job_id}} "
# protect argument quoting in squeque and sinfo sent through SSH
c.SlurmSpawner.batch_query_cmd = r"squeue -h -j {{job_id}} -o \'%T %B\' "
c.MOSlurmSpawner.slurm_info_cmd = r"sinfo -a --noheader -o \'%R %D %C %G %m\'"

# directly launch single-user server (without srun) to avoid issues with MPI software
# job environment is already reset before any step starts
c.SlurmSpawner.req_srun = ''

# expand the execution hostname returned by squeue to a FQDN
c.SlurmSpawner.state_exechost_exp = r'\1.hydra.internal.domain'

#------------------------------------------------------------------------------
# Web UI template configuration
#------------------------------------------------------------------------------
# Paths to search for jinja templates, before using the default templates.
c.JupyterHub.template_paths = ["/home/jupyterhub/.config/templates"]
