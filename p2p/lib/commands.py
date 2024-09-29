from enum import Enum

class Command(Enum):
    CONNECT = b"CON:"
    UPLOAD = b"UPL:"
    DOWNLOAD = b"DOW:"
    TERMINATE = b"TER:"
    ACKNOWLEDGE = b"ACK:"
    ERROR = b"ERR:"
    DATA = b"DAT:"
    TRANSFER = b"TRA:"
    PEER = b"PER:"
    INITIALIZE = b"INI:"
    RETRY = b"RET:"
    DISCONNECT = b"DIS:"
