from functools import partial
from time import time


class Scheduler:
    def __init__(self):
        self.tasks = []

    def loop(self):
        """
        Run tasks if they're due to run.
        :return: None
        :rtype: NoneType
        """
        tasks_run = []
        for task in filter(lambda t: t.should_run(), self.tasks):
            task.run()
            tasks_run.append(task)
        for task in tasks_run:
            self.tasks.remove(task)

    def add_task(self, task):
        """
        Add a task to the scheduler.
        :param task: Task to run some time in the future.
        :type task: Task
        :return: None
        :rtype: NoneType
        """
        self.tasks.append(task)


class Task:
    def __init__(self, run_after, function, *args, **kwargs):
        """
        Initialise a new task to run after a given time.
        :param run_after: Unix timestamp to run the task after, from time()
        :type run_after: float
        :param function: Function to call with *args and **kwargs
        :type function: Function
        """
        self.run_after = run_after
        self.function = partial(function, *args, **kwargs)

    def should_run(self):
        """
        Checks if the task should run yet.
        :return: True if the current time is >= self.run_after
        :rtype: bool
        """
        return time() >= self.run_after

    def run(self):
        """
        Runs the task.
        :return: The return value of the function.
        """
        return self.function()
