from enum import Enum

class Command(Enum):
    CONNECT = b"CON:"
    UPLOAD = b"UPL:"
    DOWNLOAD = b"DOW:"
    TERMINATE = b"TER:"
    ACKNOWLEDGE = b"ACK:"
