from enum import StrEnum


class Hostname:
    FILE_LEECH_WORKER = 'FILE_LEECH_WORKER'
    FILE_SYNC_WORKER = 'FILE_SYNC_WORKER'
    LINK_PARSE_WORKER = 'LINK_PARSE_WORKER'


class Project:
    LEECH_DOWNLOADER = 'module.leech.adaptors.downloader'
    LEECH_UPLOADER = 'module.leech.adaptors.uploader'
    LEECH_PARSER = 'module.leech.adaptors.parser'


class Queue:
    FILE_DOWNLOAD_QUEUE = 'FILE_DOWNLOAD_QUEUE'
    FILE_SYNC_QUEUE = 'FILE_SYNC_QUEUE'
    LINK_PARSE_QUEUE = 'LINK_PARSE_QUEUE'


class WorkerStatus(StrEnum):
    SETUP_BEFORE_RUN = 'SETUP_BEFORE_RUN'
    READY = 'READY'
    SHUTDOWN = 'SHUTDOWN'
