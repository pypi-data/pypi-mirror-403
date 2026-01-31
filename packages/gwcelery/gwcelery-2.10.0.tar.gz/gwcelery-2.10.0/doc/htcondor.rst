.. highlight:: shell-session

Running under HTCondor
======================

The recommended way to start and stop GWCelery on the LIGO Data Grid cluster is
using HTCondor_ DAGMan. GWCelery uses the `ezdag`_ library to dynamically
generate HTCondor DAG (Directed Acyclic Graph) files that orchestrate all
worker processes, the Flask web application, and Flower.

Prerequisites
-------------

To run GWCelery under HTCondor, you must:

1. Install GWCelery with the ``[condor]`` extra to include ``ezdag`` and the
   HTCondor Python bindings::

    $ uv sync --extra condor

2. Start the Redis server yourself (e.g. via systemd); see the
   :ref:`Redis configuration section <redis-configuration>` for details.

DAG-based Architecture
----------------------

GWCelery uses HTCondor DAGMan to manage its worker processes. When you run
``gwcelery condor submit``, it dynamically generates a DAG file along with
individual submit files for each component. These files are written to
``.local/state/dag/`` in your current directory.

The DAG includes the following nodes (see :doc:`design` for more information on
the nodes).

* **gwcelery-beat**: Celery beat scheduler for periodic tasks
* **gwcelery-worker**: Main Celery worker for general tasks
* **gwcelery-flask**: Flask web application
* **gwcelery-flower**: Flower monitoring dashboard
* **gwcelery-voevent-worker**: Worker for VOEvent processing
* **gwcelery-kafka-worker**: Worker for IGWN Alert/Kafka message handling
* **gwcelery-exttrig-worker**: Worker for external trigger processing
* **gwcelery-superevent-worker**: Worker for superevent management
* **gwcelery-embright-worker**: Worker for em-bright calculations
* **gwcelery-highmem-worker**: Worker for high-memory tasks
* **gwcelery-multiproc-worker**: Multiprocessing worker
* **gwcelery-openmp-worker-01** through **gwcelery-openmp-worker-15**: 15 parallel
  OpenMP workers for BAYESTAR sky localization

Log files are written to ``.local/state/dag/log/`` with names like
``gwcelery-worker-<cluster>-<process>.out`` and ``.err``.

Starting GWCelery
-----------------

Navigate to the directory where you want log files and DAG state to be stored::

    $ mkdir -p ~/gwcelery && cd ~/gwcelery

Then submit the DAG using the gwcelery command::

    $ gwcelery condor submit

This creates the DAG files in ``.local/state/dag/`` and submits the DAGMan job
to HTCondor. The DAGMan job will then submit all the individual worker jobs.

Stopping and Restarting GWCelery
---------------------------------

To stop GWCelery, use the ``gwcelery condor rm`` command::

    $ gwcelery condor rm

To hold (pause) GWCelery jobs, run the ``condor_hold`` command::

    $ condor_hold -constraint 'JobBatchName == "gwcelery" && JobUniverse != 7'

To release (resume) held jobs, run ``condor_release``::

    $ condor_release -constraint 'JobBatchName == "gwcelery" && JobUniverse != 7'

Note that there is normally **no need** to re-submit GWCelery if the machine is
rebooted, because the jobs will persist in the HTCondor queue.

.. _HTCondor: https://research.cs.wisc.edu/htcondor/
.. _ezdag: https://ezdag.readthedocs.io/

Shortcuts
---------

The following commands are provided as shortcuts for the above operations::

    $ gwcelery condor submit       # Submit the DAG to HTCondor
    $ gwcelery condor rm           # Remove all GWCelery jobs
    $ gwcelery condor q            # Query status of GWCelery jobs
    $ gwcelery condor hold         # Hold (pause) all GWCelery jobs
    $ gwcelery condor release      # Release (resume) all held GWCelery jobs

The following command is a shortcut for
``gwcelery condor rm; gwcelery condor submit``::

    $ gwcelery condor resubmit     # Remove and re-submit GWCelery

Managing multiple deployments
-----------------------------

There should generally be at most one full deployment of GWCelery per GraceDB
server running at one time. The ``gwcelery condor`` shortcut command is
designed to protect you from accidentally starting multiple deployments of
GWCelery by inspecting the HTCondor job queue before submitting new jobs. If
you try to start GWCelery a second time on the same host in the same directory,
you will get the following error message::

    $ gwcelery condor submit
    error: GWCelery jobs are already running in this directory.
    First remove existing jobs with "gwcelery condor rm".
    To see the status of those jobs, run "gwcelery condor q".

However, there are situations where you may actually want to run multiple
instances of GWCelery on the same machine. For example, you may want to run one
instance for the 'production' GraceDB server and one for the 'playground'
server. To accomplish this, just start the two instances of gwcelery in
different directories. Here is an example::

    $ mkdir -p production
    $ pushd production
    $ CELERY_CONFIG_MODULE=gwcelery.conf.production gwcelery condor submit
    $ popd
    $ mkdir -p playground
    $ pushd playground
    $ CELERY_CONFIG_MODULE=gwcelery.conf.playground gwcelery condor submit
    $ popd

Job accounting
--------------

When GWCelery is started using ``gwcelery condor submit`` or ``gwcelery condor
resubmit``, the :ref:`HTCondor accounting group
<htcondor:admin-manual/user-priorities-negotiation:group accounting>` is set
based on which GWCelery configuration you are using:

* ``ligo.prod.o3.cbc.pe.bayestar`` for production
* ``ligo.dev.o3.cbc.pe.bayestar`` for all other configurations, including
  playground
