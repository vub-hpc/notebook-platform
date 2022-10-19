# JupyterHub

![JupyterHub integration in HPC cluster](jupyterhub-diagram.png "JupyterHub integration in HPC cluster")

The hub and its HTTP proxy are run by a non-root user in a rootless container.
The container is managed by a service in [systemd](https://systemd.io/) with
[podman](https://podman.io/).

Notebooks are run remotely, in any available compute node in the HPC cluster.
The allocation of hardware resources for the notebook is done on-demand by
[Slurm](https://slurm.schedmd.com/). JupyterHub can submit jobs to Slurm to
launch new notebooks thanks to [batchspawner](https://github.com/jupyterhub/batchspawner).
The main particularity of our setup is that such jobs are not submitted to
Slurm from the host running JupyterHub, but from the login nodes of the HPC
cluster.

## Network

The network setup for JupyterHub is rather simple. Rootless containers do not
have a routable IP address, so they rely on the network interfaces of the host
system. The hub must be able to talk to the notebooks being executed on the
compute nodes in the internal network, as well as serve the HTTPS requests
(through its proxy) from users on the external network. Therefore, ports 8000
(HTTP proxy) and 8081 (REST API) in the
[container are forwarded to the host system](usr/local/bin/jupyterhub-init.sh#L54).

The firewall on the host systems blocks all connection through the external
network interface and forwards port 8000 on the internal interface (HTTP proxy)
to port 443 on the external one. This setup allows accessing the web interface
of the hub/notebooks from both the internal and external networks. The REST API
of the hub is only available on port 8081 of the internal network.

## Authentication

User authentication is handled through delegation via the
[OAuth](https://en.wikipedia.org/wiki/OAuth) service of the
[VSC](https://www.vscentrum.be/) accounts used by our users.

We made a custom
[VSCGenericOAuthenticator](etc/jupyterhub/jupyterhub_config.py#L73-L77) which
is heavily based on `LocalGenericOAuthenticator` from
[OAuthenticator](https://github.com/jupyterhub/oauthenticator/):

* entirely relies on OAuthenticator to carry out a standard OAuth delegation
  with the VSC account page, the [URLs of the VSC OAuth are defined in the
  environment of the container](container/Dockerfile#L59-L61) and the [secrets
  to connect to it are defined in JupyterHub's configuration
  file](etc/jupyterhub/jupyterhub_config.py#L83-L88)
* automatically creates local users in the container for any VSC account logged
  in to JupyterHub and ensures correct UID mapping to allow local VSC users to
  [access their home directories](usr/local/bin/jupyterhub-init.sh#L80),
  which is needed to securely connect to the login nodes in the HPC cluster
  with their SSH keys

## Rootless

JupyterHub is run by a non-root user in a rootless container. Setting up a
rootless container is well described in the [podman rootless
tutorial](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md).

We use a [system service](etc/systemd/system/jupyterhub.service) to execute
`podman` by a non-root user `jupyterhub` (*aka* JupyterHub operator). This
service relies on a [custom shell script](usr/local/bin/jupyterhub-init.sh) to
automatically initialize a new image of the rootless container or start an
existing one.

### Extra permissions

In the current setup, running JupyterHub fully non-root is not possible because
the hub needs superuser permissions for two specific tasks:

* `VSCGenericOAuthenticator` creates local users in the container
* `SlurmSpawner` switches to VSC users (other non-root users) to launch their
  notebooks through Slurm

These additional permissions are granted to the hub user discretely by means of
`sudo`. The definitions of each extra permission is defined in the
[sudoers](container/sudoers.conf) file of the container.

### Container namespace

Users logging in JupyterHub have to access their home directories to be able to
connect to the login nodes of the HPC cluster with their SSH keys. Since home
directories are bound to the mounts in the host system, it is critical to
properly define the namespace used by the rootless container to cover the real
UIDs of the users in the host system.

The UID/GIDs of VSC users are all in the 250000-2599999 range. We can
easily create a [mapping for the container](etc/subuid) with a straightforward
relationship between the UIDs inside and outside the container:

```
$ podman unshare cat /proc/self/uid_map
         0       4009          1
         1    2500001      65536
```

Therefore, the non-root user executing the rootless container will be mapped to
the root user of the container, as usual. While, for instance, user with UID 1
in the container will be able to access the files of UID 250001 outside.
The custom method [`vsc_user_uid_home`](etc/jupyterhub/jupyterhub_config.py#L43)
ensures that VSC users created inside the container have the correct UID with
regards to this mapping.

The namespace used by the container must be available in the host system (*i.e*
not assigned to any user or group in the system), which means that the VSC
users must not exist in the host system of the container. This requirement does
not hinder mounting the home directories of those VSC users in the system
though, as any existing files owned by those UID/GIDs of the VSC users will be
just non-assigned to any known user/group.

## Slurm

Integration with Slurm is leveraged by `SlurmSpawner` of
[batchspawner](https://github.com/jupyterhub/batchspawner).

We modified the submission command to execute `sbatch` in the login nodes of
the HPC cluster through SSH. The login nodes already run Slurm and are the sole
systems handling job submission in our cluster. Delegating job submission to
them avoids having to install and configure Slurm in the container running
JupyterHub.

The user's environment in the hub is passed through the SSH connection by
selectively selecting the needed environment variables to launch the user's
notebook:

```
sudo -E -u vscXXXXX ssh -o 'StrictHostKeyChecking no' login.host.domain \ 
    env JUPYTERHUB_API_TOKEN="${JUPYTERHUB_API_TOKEN@Q}" \ 
    JPY_API_TOKEN="${JPY_API_TOKEN@Q}" \ 
    JUPYTERHUB_CLIENT_ID="${JUPYTERHUB_CLIENT_ID@Q}" \ 
    JUPYTERHUB_HOST="${JUPYTERHUB_HOST@Q}" \ 
    JUPYTERHUB_API_URL="${JUPYTERHUB_API_URL@Q}" \ 
    JUPYTERHUB_OAUTH_CALLBACK_URL="${JUPYTERHUB_OAUTH_CALLBACK_URL@Q}" \ 
    JUPYTERHUB_OAUTH_SCOPES="${JUPYTERHUB_OAUTH_SCOPES@Q}" \ 
    JUPYTERHUB_USER="${JUPYTERHUB_USER@Q}" \ 
    JUPYTERHUB_SERVER_NAME="${JUPYTERHUB_SERVER_NAME@Q}" \ 
    JUPYTERHUB_ACTIVITY_URL="${JUPYTERHUB_ACTIVITY_URL@Q}" \ 
    JUPYTERHUB_BASE_URL="${JUPYTERHUB_BASE_URL@Q}" \ 
    JUPYTERHUB_SERVICE_PREFIX="${JUPYTERHUB_SERVICE_PREFIX@Q}" \ 
    JUPYTERHUB_SERVICE_URL="${JUPYTERHUB_SERVICE_URL@Q}" \ 
    sbatch --parsable
```

Note: the expansion operator `${var@Q}` is available in bash 4.4+ and returns a
quoted string with escaped special characters

