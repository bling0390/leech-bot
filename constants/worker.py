from enum import StrEnum


class Hostname:
    FILE_LEECH_WORKER = 'FILE_LEECH_WORKER'
    FILE_SYNC_WORKER = 'FILE_SYNC_WORKER'


class Project:
    LEECH_DOWNLOADER = 'module.leech.adaptors.downloader'
    LEECH_UPLOADER = 'module.leech.adaptors.uploader'


class Queue:
    FILE_DOWNLOAD_QUEUE = 'FILE_DOWNLOAD_QUEUE'
    FILE_SYNC_QUEUE = 'FILE_SYNC_QUEUE'


class WorkerStatus(StrEnum):
    SETUP_BEFORE_RUN = 'SETUP_BEFORE_RUN'
    READY = 'READY'
    SHUTDOWN = 'SHUTDOWN'
