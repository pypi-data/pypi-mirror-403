import src.mrodent_lib.configure_logging as configure_logging
# import src.mrodent_lib.conflog_test as conflog_test
import logging

configure_logging('mouse_trials2')
# conflog_test.configure_logging('mouse_trials')

mouse_logger = logging.getLogger('mouse_trials2')

mouse_logger.info(f'+++ A')

mouse_logger.warning(f'+++ B')

mouse_logger.error(f'+++ ERROR')

crit_msg = """
+++ CRITICAL
bumbles
blee
"""
mouse_logger.critical(crit_msg)


def exception_raising_func():
    raise Exception('bobbles')
def outer_exception_raising_func():
    try:
        exception_raising_func()
    except BaseException:
        mouse_logger.exception('exception message') 
outer_exception_raising_func()