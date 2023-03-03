# Notebook platform of VUB-HPC

The goal of our notebook platform is to provide a web-based interface to our
tier-2 HPC cluster. This alternative interface to the standard shell interface
is based on [computational notebooks](https://en.wikipedia.org/wiki/Notebook_interface).
The notebook platform must be capable to:
* handle VSC user authentication
* allow selection of computational resources
* launch notebooks leveraging the computational resources of our HPC infrastructure
* allow users to manage a library of notebooks
* integrate with the software module system of our HPC clusters

## JupyterHub

![JupyterHub integration in HPC cluster](jupyterhub/jupyterhub-diagram.png "JupyterHub integration in HPC cluster")

[JupyterHub](https://jupyter.org/hub) from the Jupyter Project fulfills all
requirements of this platform. Moreover, the modular architecture of JupyterHub
allows to easily implement solutions for those requirements that are not
covered natively. The details of its integration in the HPC cluster of VUB are
available in [notebook-platform/jupyterhub](jupyterhub).

