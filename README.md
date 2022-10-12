# Notebook platform of VUB-HPC

The goal of our notebook platform is to provide a web-based interface to our
tier-2 HPC cluster. This alternative interface to the standard shell interface
is based on [computational notebooks](https://en.wikipedia.org/wiki/Notebook_interface).
The notebook platform must be capable to handle user authentication, launch
notebooks leveraging the computational resources of our HPC infrastructure and
allow users to manage a library of notebooks.

## JupyterHub

[JupyterHub](https://jupyter.org/hub) from the Jupyter Project fulfills all the
requirements of this platform. The details of its integration in the HPC
cluster of VUB are available in [notebook-platform/jupyterhub](jupyterhub).

