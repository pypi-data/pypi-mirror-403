"""
Logger
------
Really simple logger class, originally created for the
https://github.com/uaf-arctic-eco-modeling/Input_production
project

"""
from dataclasses import dataclass, field
from enum import Enum
from collections import UserList
from datetime import datetime
from pathlib import Path

## message types 
MsgType = Enum(
    'MsgType', 
    [('debug', 0 ), ('info', 1), ('warn', 2), ('error', 3)]
)

## Message levels
ERROR = [MsgType.error]
WARN  = ERROR + [MsgType.warn]
INFO  = WARN  + [MsgType.info]
DEBUG = INFO  + [MsgType.debug] 


@dataclass
class LogMsg:
    """Simple class to store each message

    Attributes
    ----------
    text: str
        log message text
    msg_type: MsgType
        type of message
    time: datetime
        time of message
    """
    text: str
    msg_type: MsgType
    time: datetime = field(default_factory=datetime.now)


class MalformedLogMsgError(Exception):
    """Error raised if message is broken
    """
    pass

class Logger(UserList):
    """Simple logger class

    Attributes
    ----------
    data: list of LogMsg
        the messages
    verbose_levels: list of MsgType
        MsgTypes to print to console
    _suspended_levels: list of MsgType
        Internal attribute for temporary storage of `verbose_levels`
        when `suspend` is called
    """
    def __init__(self, data: list = [], verbose_levels = []):
        """Initializer

        Parameters
        ----------
        data: list of LogMsg, Optional
            Initial list of messages
        verbose_levels: list of MsgType, Optional
            MsgTypes to print to console, if not provided,
            messages are not printed, but can be saved later.
        """
        self.data = data
        self.verbose_levels = verbose_levels
        self._suspended_levels = []

    def suspend(self):
        """Temporarily suspend printing of messages
        """
        self._suspended_levels = self.verbose_levels
        self.verbose_levels = []

    def resume(self):
        """Resume printing of messages
        """
        self.verbose_levels = self._suspended_levels
        self._suspended_levels = [] 

    def clear(self):
        """Clear messages from `data`
        """
        self.data = []

    def write(self, path: Path|str, mode: str = 'w', clear: bool = True):
        """Write messages to text file

        Parameters
        ----------
        path: Path
            Path to text file
        mode: str, defaults 'w'
            File mode 'w' or 'a' for write or append
        clear: bool, defaults True
            If true, calls `clear` after writing messages
        """
        if type(path) is str:
            path = Path(path)

        with path.open(mode) as fd:
            for item in self:
                fd.write(f'{item.msg_type.name.upper()} [{item.time}]: {item.text}\n')

        if clear: self.clear()

    def append(self, item: LogMsg):
        """Appends message to `data`

        Parameters
        ----------
        item: LogMsg
            new message


        Raises
        ------
        MalformedLogMsgError: 
            When item is not LogMsg
        """
        if not isinstance(item, LogMsg):
            raise MalformedLogMsgError('Only LogMsg Items may be appended')
        else:
            if item.msg_type in self.verbose_levels:
                print(f'{item.msg_type.name.upper()} [{item.time}]: {item.text}')
            super().append(item)

    def log(self, text:str, msg_type: MsgType = MsgType.info):
        """Add Generic messge to log 

        Parameters
        ----------
        text: str
            text of message
        msg_type: MsgType, defaults MsgType.info
            message type
        """
        self.append(LogMsg(text, msg_type))

    def debug(self, text:str):
        """Adds debug message

        Parameters
        ----------
        text: str
            text of message
        """
        self.log(text, MsgType.debug)

    def info(self, text:str):
        """Adds info message

        Parameters
        ----------
        text: str
            text of message
        """
        self.log(text, MsgType.info)

    def warn(self, text:str):
        """Adds warning message

        Parameters
        ----------
        text: str
            text of message
        """
        self.log(text, MsgType.warn)
    
    def error(self, text:str):
        """Adds error message

        Parameters
        ----------
        text: str
            text of message
        """
        self.log(text, MsgType.error)
