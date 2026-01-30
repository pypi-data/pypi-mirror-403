from threading import Thread


class ParallelRunner:
    """
    A runner which runs various transfer operations in parallel.
    """

    def __init__(self):
        self.processes = []

    def add(self, name, function, *args, **kwargs):
        """
        Adds any function to the list of functions to be run in parallel

        Args:
            name (str): The process unique name
                        If exception happens, it shows the exception belongs to which process.
            function (obj: function): the function to be run in parallel
            args: Any arguments which need to be passed to the function at runtime
            kwargs: Any key word arguments which need to be passed to the function at runtime

        Example:
            >>> from tmg.data import runner
            >>> parallel_runner = runner.ParallelRunner()
            >>> parallel_runner.add('sample_process_1', sample_function, 'sample.csv', sample_keyword=True)
        """
        self.processes.append((name, function, list(args), kwargs))

    def run(self, wait_for_result=False):
        """
        Runs the list of processes in this object in parallel.

        Args:
            wait_for_result (bool, Optional): Determines whether to wait for all the processes to finish before returning from this function

        Example:
            >>> from tmg.data import runner
            >>> parallel_runner = runner.ParallelRunner()
            >>> parallel_runner.add('sample_function_1', sample_function, 'sample.csv', sample_keyword=True)
            >>> parallel_runner.run(wait_for_result=True)
        """
        threads = [
            ThreadWithReturnValue(name=process[0], target=process[1], args=process[2], kwargs=process[3])
            for process in self.processes
        ]
        for thread in threads:
            thread.start()
        if wait_for_result:
            results = []
            for thread in threads:
                try:
                    results.append(thread.join())
                except Exception as e:
                    raise e
            return results


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)

        self._return = None
        self._exc = None

    def run(self):
        self._exc = None
        if self._target is not None:
            try:
                self._return = self._target(*self._args, **self._kwargs)
            except BaseException as e:
                self._exc = e

    def join(self):
        Thread.join(self)
        if self._exc:
            raise self._exc
        return self._return
