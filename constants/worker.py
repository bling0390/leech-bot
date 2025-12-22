from enum import StrEnum


class Hostname:
    FILE_LEECH_WORKER = 'FILE_LEECH_WORKER'
    FILE_SYNC_WORKER = 'FILE_SYNC_WORKER'
    FILE_NOTIFY_WORKER = 'FILE_NOTIFY_WORKER'


class Project:
    LEECH_DOWNLOADER = 'module.leech.adaptors.downloader'
    LEECH_UPLOADER = 'module.leech.adaptors.uploader'
    LEECH_NOTIFIER = 'module.leech.adaptors.notifier'


class Queue:
    FILE_DOWNLOAD_QUEUE = 'FILE_DOWNLOAD_QUEUE'
    FILE_SYNC_QUEUE = 'FILE_SYNC_QUEUE'
    FILE_NOTIFY_QUEUE = 'FILE_NOTIFY_QUEUE'


class WorkerStatus(StrEnum):
    SETUP_BEFORE_RUN = 'SETUP_BEFORE_RUN'
    READY = 'READY'
    SHUTDOWN = 'SHUTDOWN'
