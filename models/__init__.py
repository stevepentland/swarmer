from collections import namedtuple

from .runner_cfg import RunnerConfig

TaskEntry = namedtuple('TaskEntry', ['identifier', 'name', 'args', 'image', 'task_id', 'started'])
RunnableTask = namedtuple('RunnableTask', ['identifier', 'name', 'args', 'image'])
