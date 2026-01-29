import logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%H:%M:%S', level=logging.DEBUG)
basic_logger = logging.getLogger('BASIC')
basic_logger.info(f'start {__file__}')

import pathlib, os, sys, re

IS_LINUX = None
if sys.platform.lower().startswith('lin'):
    IS_LINUX = True
elif sys.platform.lower().startswith('win'):
    IS_LINUX = False
else:
    basic_logger.error(f'FATAL. Unknown operating system: |{sys.platform}|')
    sys.exit()

PART2_NAME = 'PART2'
PART2_VAL = os.environ.get(PART2_NAME)
if PART2_VAL == None:
    basic_logger.error(f'FATAL. Environment variable |{PART2_NAME}| not set')
    sys.exit()

basic_logger.info(f'+++ PART2_VAL {PART2_VAL}')

# basic_logger.info(f'+++ pathlib.Path.cwd() {pathlib.Path.cwd()} type {type(pathlib.Path.cwd())}')
cwd_parts = pathlib.Path.cwd().parts
# basic_logger.info(f'+++ cwd_parts |{cwd_parts}| cwd_parts[-2].lower() |{cwd_parts[-2].lower()}|')
IS_PRODUCTION = None
if re.match('.*workspace.*', cwd_parts[-2].lower()):
    # basic_logger.info(f'+++ A')
    IS_PRODUCTION = False
elif cwd_parts[-2].lower() == 'operative':
    # basic_logger.info(f'+++ A')
    IS_PRODUCTION = True
if IS_PRODUCTION is None:
    basic_logger.error(f'FATAL. CWD is {cwd_parts}: this indicates neither a production run nor a dev run')
    sys.exit()
# logging_directory_str = f'{"ephem" if IS_PRODUCTION else "temp"}/logging' 
# basic_logger.info(f'+++ PART2_VAL {PART2_VAL} type {type(PART2_VAL)}')
# STANDARD_LOGGING_LOCATION = pathlib.Path(PART2_VAL, logging_directory_str)

logging_directory_str = f'{"ephem" if IS_PRODUCTION else "temp"}' 

if IS_LINUX:

    STANDARD_LOGGING_LOCATION = pathlib.Path(PART2_VAL, logging_directory_str, 'logging')

else:
    STANDARD_LOGGING_LOCATION = pathlib.Path(PART2_VAL, '/', logging_directory_str, 'logging')

basic_logger.info(f'+++ STANDARD_LOGGING_LOCATION {STANDARD_LOGGING_LOCATION}')