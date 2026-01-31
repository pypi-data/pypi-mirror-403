import enum
import os


@enum.unique
class JobStatus(enum.IntEnum):
    """Job status codes describing the current status of a job

    * WAITING_INFO : Waiting for status from the job. Job has not started yet computation.
    * RUNNING : Job is currently running
    * COMPLETED : Job has successfully completed
    * ERROR : Job has exited with an error
    """

    WAITING_INFO = 0
    RUNNING = 1
    COMPLETED = 2
    ERROR = 3

    def describe(self):
        codes = {0: "Waiting info", 1: "Running", 2: "Completed", 3: "Error"}
        return codes[self.value]

    def __str__(self):
        return self.describe()


class ExecutableDirectory:
    """Executable directory class.

    All app functions will create a folder and return to you an `ExecutableDirectory` object.
    This is a self-contained directory including all app input files which can be executed either locally or on a cluster.
    If it's not executed locally make sure the directory can be accessed from all machines
    in the cluster (i.e. is located on a shared filesystem).
    """

    def __init__(
        self,
        dirname,
        inputs_dir=None,
        _execution_resources=None,
        _input_json=None,
        _execution_backend=None,
    ) -> None:
        self.dirname = dirname

        if inputs_dir is None:
            # Find all the run_ folders in the directory and use the most recent one
            run_folders = [
                f
                for f in os.listdir(dirname)
                if f.startswith("run_") and os.path.isdir(os.path.join(dirname, f))
            ]
            run_folders.sort(key=lambda x: os.path.getmtime(os.path.join(dirname, x)))
            inputs_dir = os.path.join(dirname, run_folders[-1])

        self.runsh = os.path.basename(inputs_dir) + ".sh"
        self.inputs_dir = inputs_dir

        self.execution_resources = _execution_resources
        self.slurmq = None
        self._input_json = _input_json
        self._execution_backend = _execution_backend
        self._job_id = None

    def _get_backend(self):
        """Get the execution backend, from stored value or config."""
        from playmolecule._config import _get_config
        from playmolecule._backends import _get_execution_backend
        from playmolecule._backends._local import _LocalExecutionBackend

        if self._execution_backend is not None:
            return self._execution_backend

        config = _get_config()
        backend = _get_execution_backend(config.app_root)

        # Fall back to local backend if no backend found
        if backend is None:
            backend = _LocalExecutionBackend(config.app_root or "")

        return backend

    @property
    def status(self):
        """Returns current status of the ExecutableDirectory

        Examples
        --------
        >>> ed = proteinprepare(outdir="test", pdbid="3ptb")
        >>> ed.slurm(ncpu=1, ngpu=0)
        >>> print(ed.status)
        """
        from playmolecule._backends._http import _HTTPExecutionBackend

        backend = self._get_backend()

        # Delegate to appropriate backend
        if isinstance(backend, _HTTPExecutionBackend):
            if self._job_id is None:
                raise RuntimeError("Job ID is not set. Please run the job first.")
            return backend.get_status(self.dirname, self._job_id)
        else:
            # Local backend
            return backend.get_status(self.dirname, self.inputs_dir, self.slurmq)

    def run(self, queue=None, verbose=True, **kwargs):
        """Execute the directory locally

        If no queue is specified it will run the job locally.

        Examples
        --------
        >>> ed = proteinprepare(outdir="test", pdbid="3ptb")
        >>> ed.run()

        Specifying a queue

        >>> ed.run(queue="slurm", partition="normalCPU", ncpu=3, ngpu=1)

        Alternative syntax for

        >>> ed.slurm(partition="normalCPU", ncpu=3, ngpu=1)
        """
        from playmolecule._config import _get_config
        from playmolecule._backends._http import _HTTPExecutionBackend

        config = _get_config()

        if queue is None and config.queue_config is not None:
            qconf = dict(config.queue_config)
            queue = qconf["queue"].lower()
            del qconf["queue"]
            if queue == "slurm":
                # If it's SLURM try to pick the appropriate partition depending on the number of GPUs
                needs_gpu = self.execution_resources.get("ngpu", 0) > 0
                partition = (
                    qconf["gpu_partition"] if needs_gpu else qconf["cpu_partition"]
                )
                del qconf["gpu_partition"]
                del qconf["cpu_partition"]
                qconf["partition"] = partition
            kwargs = qconf

        self.slurmq = None  # New execution. Set to None

        backend = self._get_backend()

        # HTTP backend
        if isinstance(backend, _HTTPExecutionBackend):
            self._job_id = backend.run(self.dirname, self._input_json, **kwargs)
            return

        # Local execution
        if queue is None:
            backend.run(self.dirname, self.runsh, verbose=verbose)
        elif queue.lower() == "slurm":
            self.slurm(**kwargs)

    def slurm(self, **kwargs):
        """Submit simulations to SLURM cluster

        Parameters
        ----------
        partition : str or list of str
            The queue (partition) or list of queues to run on. If list, the one offering earliest initiation will be used.
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
            Only run on GPUs with at least this much memory. Needs special setup of SLURM. Check how to define gpu_mem on
            SLURM.
        walltime : int
            Job timeout (s)
        mailtype : str
            When to send emails. Separate options with commas like 'END,FAIL'.
        mailuser : str
            User email address.
        outputstream : str
            Output stream.
        errorstream : str
            Error stream.
        nodelist : list
            A list of nodes on which to run every job at the *same time*! Careful! The jobs will be duplicated!
        exclude : list
            A list of nodes on which *not* to run the jobs. Use this to select nodes on which to allow the jobs to run on.
        envvars : str
            Envvars to propagate from submission node to the running node (comma-separated)
        prerun : list
            Shell commands to execute on the running node before the job (e.g. loading modules)

        Examples
        --------
        >>> ed = proteinprepare(outdir="test", pdbid="3ptb")
        >>> ed.slurm(partition="normalCPU", ncpu=1, ngpu=0)
        """
        from playmolecule._backends._slurm import _submit_slurm

        self.slurmq = _submit_slurm(
            self.dirname, self.runsh, self.execution_resources, **kwargs
        )
