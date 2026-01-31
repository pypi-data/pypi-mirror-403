# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""SLURM execution backend."""

from typing import Any, Dict, List, Optional
from playmolecule._public_api import JobStatus


def _submit_slurm(
    dirname: str,
    runsh: str,
    execution_resources: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """Submit a job to SLURM.

    Parameters
    ----------
    dirname : str
        Directory containing the run script
    runsh : str
        Run script filename
    execution_resources : dict, optional
        Default execution resources from app manifest
    **kwargs
        Additional SLURM options (partition, ncpu, ngpu, etc.)

    Returns
    -------
    SlurmQueue
        The SLURM queue object
    """
    from jobqueues.slurmqueue import SlurmQueue

    sl = SlurmQueue()
    sl.runscript = runsh

    # Set app defaults
    if execution_resources is not None:
        for arg in execution_resources:
            setattr(sl, arg, execution_resources[arg])

    # Set user-specified arguments
    for arg in kwargs:
        setattr(sl, arg, kwargs[arg])

    sl.submit(dirname)
    return sl


def _get_slurm_status(slurmq: Any) -> JobStatus:
    """Get job status from SLURM queue.

    Parameters
    ----------
    slurmq : SlurmQueue
        The SLURM queue object

    Returns
    -------
    JobStatus
        Current job status
    """
    from jobqueues.simqueue import QueueJobStatus

    mapping = {
        QueueJobStatus.RUNNING: JobStatus.RUNNING,
        QueueJobStatus.FAILED: JobStatus.ERROR,
        QueueJobStatus.CANCELLED: JobStatus.ERROR,
        QueueJobStatus.OUT_OF_MEMORY: JobStatus.ERROR,
        QueueJobStatus.TIMEOUT: JobStatus.ERROR,
        QueueJobStatus.COMPLETED: JobStatus.COMPLETED,
        QueueJobStatus.PENDING: JobStatus.WAITING_INFO,
        None: JobStatus.WAITING_INFO,
    }

    info = slurmq.jobInfo()
    if info is None:
        return JobStatus.WAITING_INFO

    return mapping[info[list(info.keys())[0]]["state"]]


def slurm_mps(exec_dirs: List[Any], **kwargs) -> Any:
    """Submit a list of ExecutableDirectories to SLURM as a single MPS job.

    This means that all jobs submitted will be executed on the same GPU.

    Parameters
    ----------
    exec_dirs : list[ExecutableDirectory]
        An iterable of ExecutableDirectory objects
    partition : str or list of str
        The queue (partition) or list of queues to run on.
    jobname : str
        Job name (identifier)
    priority : str
        Job priority
    ncpu : int
        Number of CPUs to use for a single job
    ngpu : int
        Number of GPUs to use for a single job
    memory : int
        Amount of memory per job (MiB)
    gpumemory : int
        Only run on GPUs with at least this much memory.
    walltime : int
        Job timeout (s)
    mailtype : str
        When to send emails.
    mailuser : str
        User email address.
    outputstream : str
        Output stream.
    errorstream : str
        Error stream.
    nodelist : list
        A list of nodes on which to run every job.
    exclude : list
        A list of nodes on which *not* to run the jobs.
    envvars : str
        Envvars to propagate from submission node to the running node.
    prerun : list
        Shell commands to execute on the running node before the job.

    Returns
    -------
    SlurmQueue
        The SLURM queue object

    Examples
    --------
    >>> ed1 = kdeep(outdir="test1", ...)
    >>> ed2 = kdeep(outdir="test2", ...)
    >>> slurm_mps([ed1, ed2], partition="normalGPU", ncpu=1, ngpu=1)
    """
    from jobqueues.slurmqueue import SlurmQueue

    sl = SlurmQueue()

    # Set app defaults from first exec_dir
    if exec_dirs[0].execution_resources is not None:
        for arg in exec_dirs[0].execution_resources:
            setattr(sl, arg, exec_dirs[0].execution_resources[arg])

    # Set user-specified arguments
    for arg in kwargs:
        setattr(sl, arg, kwargs[arg])

    sl.submit(
        dirs=[ed.dirname for ed in exec_dirs],
        runscripts=[ed.runsh for ed in exec_dirs],
        nvidia_mps=True,
    )
    return sl
