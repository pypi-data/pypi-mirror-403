import logging, concurrent_log_handler, colorlog, datetime

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%H:%M:%S', level=logging.DEBUG)
basic_logger = logging.getLogger('BASIC')
basic_logger.info(f'start {__file__}')

import sys, colorlog, concurrent_log_handler

from . constants_lib import *

def configure_logging(logger_name, maxBytes = 1024 * 1024):
    logger = colorlog.getLogger(logger_name) # in fact of type logging.Logger 

    """
2026-01-23
I found out today that if you add the StreamHandler before adding the ConcurrentRotatingFileHandler, things
work OK. But if you do it in the other order, somehow the CRFH's formatter gets "influenced" by the settings of the 
StreamHandler's formatter: so, for example, I was finding that colour control codes were being printed to the log
file. I have little idea of what's going on here: something to do with "propagation" ... (?)
    """

    logger_file_path = pathlib.Path('crfh', 'rotator_fh.log')
    logger_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = concurrent_log_handler.ConcurrentRotatingFileHandler(logger_file_path, 'a', maxBytes, 10, 'utf-8')
    logger.addHandler(file_handler)
    file_handler.setFormatter(EnhancedCRFHFormatter(
        '%(asctime)s - [%(name)s] - %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s'))
    stream_handler = logging.StreamHandler(sys.stdout) # make it go to stdout
    logger.addHandler(stream_handler)
    stream_handler.setFormatter(EnhancedColourFormatter(
    '%(log_color)s%(asctime)s %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s',    
    log_colors={
        'DEBUG':    'white',
        'INFO':     'white',
        'WARNING':  'fg_bold_yellow',
        'ERROR':    'fg_bold_red',
        'CRITICAL': 'fg_bold_red,bg_white',
    }, datefmt='%a %H:%M:%S'
    ))
    """
2026-01-23
NB re the above "datefmt" string: directive "%f" doesn't seem to work... so I overrode 
EnhancedColourFormatter.formatTime() to add the milliseconds to this value as produced 
    """

    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.info(f'\n{"=" * 20}\n+++ {datetime.datetime.now()} A')
    # logger.warning(f'+++ B')
    # logger.error(f'+++ C')

class BasicEnhancedFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print milliseconds after decimal point:
        self.default_msec_format = '%s.%03d'

    def formatTime(self, record, datefmt=None):
        return_val = super().formatTime(record, datefmt=datefmt)
        # basic_logger.info(f'+++ return_val {return_val} datefmt {datefmt}')
        return return_val

class EnhancedColourFormatter(colorlog.ColoredFormatter, BasicEnhancedFormatter):
    def formatTime(self, record, datefmt=None):
        return_val = super().formatTime(record, datefmt=datefmt)
        return f'{return_val}.{int(record.msecs):03}'

class EnhancedCRFHFormatter(BasicEnhancedFormatter):
    _LINE_OF_EQUALS = 120 * '='

    def formatMessage(self, record: logging.LogRecord):
        # TODO code duplication, see above (added 2023-06-19)
        record_path = pathlib.Path(record.pathname)
        cwd_path = pathlib.Path.cwd()
        if record_path.is_relative_to(cwd_path):
            record.pathname = record_path.relative_to(cwd_path)
        formatted_msg = super().formatMessage(record)
        return f'{EnhancedCRFHFormatter._LINE_OF_EQUALS}\n{formatted_msg}\n{EnhancedCRFHFormatter._LINE_OF_EQUALS}'
