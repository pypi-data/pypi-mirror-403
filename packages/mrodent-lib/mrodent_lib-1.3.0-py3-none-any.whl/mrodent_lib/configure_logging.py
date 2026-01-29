import logging

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%H:%M:%S', level=logging.DEBUG)
basic_logger = logging.getLogger('BASIC')
basic_logger.info(f'start {__file__}')

import sys, colorlog, concurrent_log_handler

from . constants_lib import *

def configure_logging(logger_name, maxBytes = 1024 * 1024):
    logger = colorlog.getLogger(logger_name) # in fact of type logging.Logger 
    log_file_path = STANDARD_LOGGING_LOCATION.joinpath(logger_name, EnhancedCRFHFormatter.LOG_FILENAME)  # type:ignore
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
    except BaseException as e:
        basic_logger.exception(f'WARNING. Failed to create logger for project "{logger_name}": exception when trying to create logging path i.e. {log_file_path.parent}')
        """
2026-01-23
thoughts about this: it would be wrong for a failure to configure a logger to end the application run, so not sys.exit()
but also you don't just want to "swallow" the failure ... thus the idea is that the caller code decides what to do with this exception: 
typically something which will let the user know prominently that this configuration failed.        
        
        """
        raise e

    file_handler = concurrent_log_handler.ConcurrentRotatingFileHandler(log_file_path, 'a', maxBytes, 10, 'utf-8')
    # ... this file handler is also ... a StreamHandler!
    logger.addHandler(file_handler)    
    file_formatter = EnhancedCRFHFormatter('%(asctime)s - [%(name)s] - %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s')
    file_handler.setFormatter(file_formatter)
    stream_handler = logging.StreamHandler(sys.stdout) # make it go to stdout
    # basic_logger.info(f'+++ stream_handler {stream_handler} type {type(stream_handler)}')
    # basic_logger.info(f'+++ logger {logger} type {type(logger)}')
    logger.addHandler(stream_handler)
    # stream_handler.setFormatter(colorlog.ColoredFormatter(
    stream_handler.setFormatter(EnhancedColourFormatter(
        '%(log_color)s%(asctime)s %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s',
        log_colors={
            'DEBUG':    'white',
            'INFO':     'white',
            'WARNING':  'fg_bold_yellow',
            'ERROR':    'fg_bold_red',
            'CRITICAL': 'fg_bold_red,bg_white',
        }, 
        datefmt='%a %H:%M:%S'))
    """
2026-01-23
NB re the above "datefmt" string: directive "%f" doesn't seem to work... so I overrode 
EnhancedColourFormatter.formatTime() to add the milliseconds to this value as produced 
    """
    logger.propagate = False
    logger.setLevel(logging.INFO)

    # basic_logger.info(f'+++ A')
    # logger.info(f'+++ A')

class BasicEnhancedFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print milliseconds after decimal point:
        self.default_msec_format = '%s.%03d'

    def formatTime(self, record, datefmt=None):
        return_val = super().formatTime(record, datefmt=datefmt)
        # basic_logger.info(f'+++ return_val {return_val} datefmt {datefmt}')
        return return_val

class EnhancedColourFormatter(colorlog.ColoredFormatter):
    def formatTime(self, record, datefmt=None):
        return_val = super().formatTime(record, datefmt=datefmt)
        return f'{return_val}.{int(record.msecs):03}'

class EnhancedCRFHFormatter(BasicEnhancedFormatter):
    LOG_FILENAME = 'rotator_fh.log'
    _LINE_OF_EQUALS = 120 * '='

    """
2022-08-01
NB it is important to understand that these two logging handlers do not operate independently!
In fact they must be added in this order: 1) stream handler, then 2) file handler... and for example, in the
formatMessage method of the formatter of the first, it can be seen that record.pathname is set to a tweaked version 
of the path string... but this SAME record is then passed to the second handler, with this formatter: so the path 
has already been set to the "tweaked" version.
Also, the time format for the file handler's formatter must be "%(asctime)s", not "%(asctime)s.%(msecs)03d", as the 
format has already been set up for this record. Doing the above actually adds the ms string again. However, in this
second formatter you DO have to stipulate that a decimal point, not a comma, should be used for the ms part!   

2026-01-23 at the current time I'm not clear why you need a "ColoredFormatter" for a file logger... 
    """

    def formatMessage(self, record: logging.LogRecord):
        # TODO code duplication, see above (added 2023-06-19)
        record_path = pathlib.Path(record.pathname)
        cwd_path = pathlib.Path.cwd()
        if record_path.is_relative_to(cwd_path):
            record.pathname = record_path.relative_to(cwd_path)
        formatted_msg = super().formatMessage(record)
        return f'{EnhancedCRFHFormatter._LINE_OF_EQUALS}\n{formatted_msg}\n{EnhancedCRFHFormatter._LINE_OF_EQUALS}'
