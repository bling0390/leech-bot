from enum import StrEnum


class TaskType(StrEnum):
    DOWNLOAD = 'DOWNLOAD'
    UPLOAD = 'UPLOAD'


class TaskStatus(StrEnum):
    INITIAL = 'INITIAL'
    EXECUTING = 'EXECUTING'
    DONE = 'DONE'
    TERMINATED = 'TERMINATED'
