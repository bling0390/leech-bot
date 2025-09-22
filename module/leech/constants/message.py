from enum import StrEnum


class MessageStatus(StrEnum):
    INITIAL = 'INITIAL'
    ALREADY_SENT = 'ALREADY_SENT'
    DISCARD = 'DISCARD'

