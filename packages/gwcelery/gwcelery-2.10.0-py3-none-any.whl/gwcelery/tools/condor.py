"""Shortcuts for HTCondor commands to manage deployment of GWCelery on LIGO
Data Grid clusters.

These commands apply to the GWCelery instance that is
running in the current working directory.
"""
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import click
import lxml.etree

try:
    from ezdag import DAG, Argument, Layer, Node, Option
    _import_error = None
except ImportError as e:
    _import_error = e


def generate_dag_and_submit_files(config):
    """Generate DAG and submit files dynamically based on configuration.

    Parameters
    ----------
    config : dict
        Configuration dictionary containing condor settings

    Returns
    -------
    Path
        Path to the generated DAG file
    """
    # Extract key environment variables from submission environment
    base_getenv = [
        'HOME', 'USER', 'VIRTUAL_ENV', 'PATH', 'OMP_NUM_THREADS',
        'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'FLASK_RUN_PORT',
        'FLASK_URL_PREFIX', 'FLOWER_PORT', 'FLOWER_URL_PREFIX',
        'CELERY_CONFIG_MODULE', 'LAL_DATA_PATH', 'BEARER_TOKEN_FILE',
        'GWDATAFIND_SERVER'
    ]

    # OpenMP environment: remove OMP_NUM_THREADS to allow multi-threading
    openmp_getenv = [v for v in base_getenv if v != 'OMP_NUM_THREADS']

    user = os.environ['USER']

    vanilla_base_env = {
        'HTGETTOKENOPTS': (
            f"--vaultserver vault.ligo.org --issuer igwn "
            f"--role read-cvmfs-{user} "
            f"--credkey read-cvmfs-{user}/robot/{user}.ligo.caltech.edu "
            f"--nooidc"
        ),
        # NOTE: CLUSTER DEPENDENT
        'CELERY_BROKER_URL': f'redis://{user}.ldas.cit'
    }

    # Common submit file settings
    common_settings = {
        'accounting_group_user': 'cody.messick',
        'accounting_group': config['condor_accounting_group'],
        'initialdir': Path.home(),
        'log': '.local/state/log/gwcelery-condor.log',
        'on_exit_remove': False,
        'request_disk': '7GB',
        'job_max_vacate_time': 20,
        'kill_sig': 'SIGKILL',
        'max_retries': 100,
    }

    # Create DAG
    dag = DAG('gwcelery')

    # Local universe jobs
    def local_layer(name):
        """Create a local universe layer with common settings."""
        return Layer(
            executable='gwcelery',
            name=name,
            universe='local',
            log_dir='.local/state/dag/log',
            transfer_files=False,
            submit_description={
                'description': name,
                'getenv': base_getenv,
                **common_settings
            }
        )

    def worker_arguments(worker_name, queue, **kwargs):
        """Create common worker arguments.

        Parameters
        ----------
        worker_name : str
            Name of the worker (e.g., 'gwcelery-worker')
        queue : str
            Queue name (e.g., 'celery')
        **kwargs : dict
            Additional options:
            - concurrency: int (default: None, uses -c/--concurrency)
            - pool: str (default: None, uses -P/--pool)
            - prefetch_multiplier: int (default: None)
            - additional_options: list of Option objects

        Returns
        -------
        list
            List of Argument and Option objects
        """
        args = [
            Argument("command", "worker", track=False),
            Option("loglevel", "info"),
            Option("hostname", f"{worker_name}@%h"),
            Option("logfile", ".local/state/log/%n.log"),
            Option("queues", queue),
        ]

        if 'concurrency' in kwargs:
            args.append(Option("concurrency", kwargs['concurrency']))
        if 'pool' in kwargs:
            args.append(Option("pool", kwargs['pool']))
        if 'prefetch_multiplier' in kwargs:
            args.append(Option("prefetch-multiplier",
                               kwargs['prefetch_multiplier']))
        if 'additional_options' in kwargs:
            args.extend(kwargs['additional_options'])

        return args

    # gwcelery beat --logfile .local/state/log/gwcelery-beat.log
    layer = local_layer('gwcelery-beat')
    layer += Node(arguments=[
        Argument("command", "beat", track=False),
        Option("logfile", ".local/state/log/gwcelery-beat.log")
    ])
    dag.attach(layer)

    # gwcelery flask --loglevel info
    #               --logfile .local/state/log/gwcelery-flask.log
    #               run --with-threads --host 127.0.0.1
    layer = local_layer('gwcelery-flask')
    layer += Node(arguments=[
        Argument("command", "flask", track=False),
        Option("loglevel", "info"),
        Option("logfile", ".local/state/log/gwcelery-flask.log"),
        Argument("subcommand", "run", track=False),
        Option("with-threads"),
        Option("host", "127.0.0.1"),
    ])
    dag.attach(layer)

    # gwcelery flower --address=127.0.0.1
    #                 --log-file-prefix=.local/state/log/gwcelery-flower.log
    layer = local_layer('gwcelery-flower')
    layer += Node(arguments=[
        Argument("command", "flower", track=False),
        # gwcelery flower requires "=" for options
        "--address=127.0.0.1",
        "--log-file-prefix=.local/state/log/gwcelery-flower.log",
    ])
    dag.attach(layer)

    # gwcelery worker --loglevel info --hostname gwcelery-worker@%h
    #                 --logfile .local/state/log/%n.log --queues celery
    #                 --igwn-alert --email --concurrency 32
    #                 --max-memory-per-child 2097152
    layer = local_layer('gwcelery-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-worker', 'celery',
        concurrency=32,
        additional_options=[
            Option("igwn-alert"),
            Option("email"),
            Option("max-memory-per-child", 2097152)
        ]
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-exttrig-worker@%h
    #                 --logfile .local/state/log/%n.log --queues exttrig
    #                 --concurrency 1 --prefetch-multiplier 1
    layer = local_layer('gwcelery-exttrig-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-exttrig-worker', 'exttrig',
        concurrency=1,
        prefetch_multiplier=1
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-superevent-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues superevent --concurrency 1
    #                 --prefetch-multiplier 1
    layer = local_layer('gwcelery-superevent-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-superevent-worker', 'superevent',
        concurrency=1,
        prefetch_multiplier=1
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-voevent-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues voevent --pool solo
    layer = local_layer('gwcelery-voevent-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-voevent-worker', 'voevent',
        pool='solo'
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-kafka-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues kafka --pool solo
    layer = local_layer('gwcelery-kafka-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-kafka-worker', 'kafka',
        pool='solo'
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-em-bright-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues em-bright --concurrency 2
    #                 --prefetch-multiplier 1
    layer = local_layer('gwcelery-embright-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-em-bright-worker', 'em-bright',
        concurrency=2,
        prefetch_multiplier=1
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-highmem-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues highmem --concurrency 2
    #                 --prefetch-multiplier 1
    layer = local_layer('gwcelery-highmem-worker')
    layer += Node(arguments=worker_arguments(
        'gwcelery-highmem-worker', 'highmem',
        concurrency=2,
        prefetch_multiplier=1
    ))
    dag.attach(layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-multiprocessing-worker@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues multiprocessing --concurrency 1
    #                 --prefetch-multiplier 1
    multiproc_layer = Layer(
        executable='gwcelery',
        name='gwcelery-multiproc-worker',
        universe='vanilla',
        log_dir='.local/state/dag/log',
        transfer_files=False,
        submit_description={
            'description': 'gwcelery-multiprocessing-worker',
            'universe': 'vanilla',
            'environment': vanilla_base_env,
            'getenv': openmp_getenv,
            '+Online_EMFollow': True,
            'Requirements': 'TARGET.Online_EMFollow =?= True',
            'request_cpus': 'TARGET.Cpus',
            'request_memory': '16GB',
            **common_settings
        }
    )
    multiproc_layer += Node(arguments=worker_arguments(
        'gwcelery-multiprocessing-worker', 'multiprocessing',
        concurrency=1,
        prefetch_multiplier=1
    ))
    dag.attach(multiproc_layer)

    # gwcelery worker --loglevel info
    #                 --hostname gwcelery-openmp-worker-NN@%h
    #                 --logfile .local/state/log/%n.log
    #                 --queues openmp --concurrency 1
    #                 --prefetch-multiplier 1
    openmp_layer = Layer(
        executable='gwcelery',
        name='gwcelery-openmp-worker',
        universe='vanilla',
        log_dir='.local/state/dag/log',
        transfer_files=False,
        submit_description={
            'description': 'gwcelery-openmp-worker-$(worker_num)',
            'universe': 'vanilla',
            'environment': vanilla_base_env,
            'getenv': openmp_getenv,
            '+Online_EMFollow': True,
            'Requirements': 'TARGET.Online_EMFollow =?= True',
            'request_cpus': 'TARGET.Cpus',
            'request_memory': '16GB',
            **common_settings
        }
    )
    # Countdown from 15 instead of up to so that output of gwcelery condor q is
    # ordered from gwcelery-openmp-worker-01 to gwcelery-openmp-worker-15
    for i in range(15, 0, -1):
        openmp_layer += Node(
            arguments=worker_arguments(
                f'gwcelery-openmp-worker-{i:02}', 'openmp',
                concurrency=1,
                prefetch_multiplier=1
            ),
            variables={'worker_num': f'{i:02}'}
        )
    dag.attach(openmp_layer)

    # Write DAG file
    # NOTE using force when submitting the dag is dangerous if we dont first
    # confirm that gwcelery isn't already running
    # FIXME The batch-name kwarg is passed in a special format right now due to
    # a bug upstream in the htcondor python bindings
    dag.write(path=Path('.local/state/dag'), write_script=True)
    dag.submit(
        path=Path('.local/state/dag'),
        write_script=True,
        include_env=','.join(base_getenv),
        **{'batch-name': 'gwcelery'},
        force=True
    )


@click.group(help=__doc__)
def condor():
    if _import_error is not None:
        click.echo(
            "Error: The 'condor' command requires the 'condor' extra "
            "to be installed.",
            err=True
        )
        raise SystemExit(1)


def get_constraints(ignore_dagman=False, only_dagman=False):
    """Get the constraint to select GWCelery jobs.

    Parameters
    ----------
    ignore_dagman : bool
        If True, exclude the DAGMan coordinator job (JobUniverse != 7)
    only_dagman : bool
        If True, only include the DAGMan coordinator job (JobUniverse == 7)
    """
    constraint = 'JobBatchName=={} && Iwd=={}'.format(
            json.dumps('gwcelery'),  # JSON string literal escape sequences
            json.dumps(os.getcwd())  # are a close match to HTCondor ClassAds.
    )

    if only_dagman:
        # Only include DAGMan coordinator job
        constraint += ' && JobUniverse == 7'
    elif ignore_dagman:
        # Exclude DAGMan coordinator job
        constraint += ' && JobUniverse != 7'

    return '-constraint', constraint


def run_exec(*args):
    print(' '.join(shlex.quote(arg) for arg in args))
    os.execvp(args[0], args)


def running():
    """Determine if GWCelery is already running under HTCondor."""
    status = subprocess.check_output(('condor_q', '-xml', *get_constraints()))
    classads = lxml.etree.fromstring(status)
    return classads.find('.//c') is not None


@condor.command()
@click.pass_context
def submit(ctx):
    """Submit all GWCelery jobs to HTCondor (if not already running)."""
    if running():
        print('error: GWCelery jobs are already running in this directory.\n'
              'First remove existing jobs with "gwcelery condor rm".\n'
              'To see the status of those jobs, run "gwcelery condor q".',
              file=sys.stderr)
        sys.exit(1)
    else:
        # Generate DAG and submit
        generate_dag_and_submit_files(ctx.obj.app.conf)


@condor.command()
@click.pass_context
def resubmit(ctx):
    """Remove any running GWCelery jobs and resubmit to HTCondor."""
    if running():
        subprocess.check_call(
            ('condor_rm', *get_constraints(only_dagman=True))
        )
    timeout = 120
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if not running():
            break
        time.sleep(1)
    else:
        print('error: Could not stop all GWCelery jobs', file=sys.stderr)
        sys.exit(1)
    # Generate DAG and submit
    generate_dag_and_submit_files(ctx.obj.app.conf)


@condor.command()
def rm():
    """Remove all GWCelery jobs by removing the DAGMan coordinator.

    HTCondor will automatically remove all child jobs when the DAGMan
    coordinator is removed.
    """
    run_exec('condor_rm', *get_constraints(only_dagman=True))


@condor.command()
def hold():
    """Put all GWCelery jobs on hold."""
    run_exec('condor_hold', *get_constraints(ignore_dagman=True))


@condor.command()
def release():
    """Release all GWCelery jobs from hold status."""
    run_exec('condor_release', *get_constraints(ignore_dagman=True))


@condor.command()
def q():
    """Show status of all GWCelery jobs."""
    run_exec('condor_q', '-nobatch', *get_constraints())
