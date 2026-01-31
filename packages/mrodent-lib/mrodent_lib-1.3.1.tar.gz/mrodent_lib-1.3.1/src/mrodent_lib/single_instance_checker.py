import logging

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%H:%M:%S', level=logging.DEBUG)
basic_logger = logging.getLogger('BASIC')
basic_logger.info(f'start {__file__}')

import sys, os

from . constants_lib import *

"""
2022-08-21
This class is intended to detect whether an instance of this script is already running.
Used like this:
    sic = lib_main.SingleInstanceChecker(__name__)
    if sic.already_running():
        logger.error(f'FATAL. ...

2026-01-29 TODO re Linux: I worked out how to get the lock to disappear when the instance disappeared in W10, 
but not yet in Linux ...

"""        
class SingleInstanceChecker:
    def __init__(self, id):
        # NB the "id" here should be unique: a filename like "__main__.py" will I think risk a confusion 
        # between processes 
        assert type(id) == str
        pid = os.getpid()
        if IS_LINUX:
            # NB an attempt to import this in W10 (for example during testing) will raise ModuleNotFoundError
            # NB needs pip install fcntl 
            import fcntl
            self.lock = open(f"/tmp/instance_{id}.lock", 'wb')
            try:
                fcntl.lockf(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.running = False
            except IOError:
                self.running = True
        else:
            # NB an attempt to import this in Linux (for example during testing) will raise ModuleNotFoundError
            # NB needs pip install pywin32 
            import win32api, winerror, win32event # type: ignore
            self.mutexname = id
            self.lock = win32event.CreateMutex(None, False, self.mutexname)
            last_error = win32api.GetLastError()
            self.running = (last_error == winerror.ERROR_ALREADY_EXISTS)

    def already_running(self):
        return self.running
        
    def __del__(self):
        if self.lock:
            try:
                if IS_LINUX:
                    # TODO how to deal with self.lock == True in Linux? does it just "close handle" automatically?
                    # NB it may happen automatically...
                    pass
                    # raise Exception('how to close the lock of the SingleInstanceChecker in Linux? TODO')
                else:
                    try:
                        import win32api # type: ignore
                    except ImportError as e:
                        # raised 2022-09-09 during pytest testing
                        if 'likely shutting down' in str(e):
                            return
                    win32api.CloseHandle(self.lock)
            except Exception as e:
                basic_logger.exception(f'{e}')


