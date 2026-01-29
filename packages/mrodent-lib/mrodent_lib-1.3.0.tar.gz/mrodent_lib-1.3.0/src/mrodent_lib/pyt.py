import logging

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%H:%M:%S', level=logging.DEBUG)
basic_logger = logging.getLogger('BASIC')
basic_logger.info(f'start {__file__}')

import sys, subprocess, pathlib, re, traceback, datetime

BASIC_PYTEST_COMMAND = 'uv run pytest --random-order'

def main():
    """
2026-01-23
if the 2nd argument (after script path str) can be parsed as an integer number > 0 and < 21, it is assumed
this is the number of times to run the command (with all the other arguments added as extra args to "uv run")...
else, in all other cases, all arguments including the 2nd argument are passed as extra args
    """
    if len(sys.argv) > 1:
        arg2 = sys.argv[1]
        try:
            times_to_run = int(arg2)
            if times_to_run > 0 and times_to_run < 21:
                extra_args = sys.argv[2:]
                extra_args_str = ' '.join(extra_args)

                start_datetime = datetime.datetime.now()
                for _ in range(times_to_run):
                    if not run_command(extra_args_str):
                        return
                test_duration = datetime.datetime.now() - start_datetime
                total_micros = test_duration.seconds * 1000000 + test_duration.microseconds
                total_s = total_micros/1000000
                # NB ":.3f" means always show 3 decimals even if there is/are trailing zero(s)
                basic_logger.info(f'test duration seconds {round(total_s, 3):.3f}, i.e. {round(total_s/times_to_run, 3):.3f} seconds per pytest run')

                return
            else:
                explain_str = f"""the number passed as the param after "pyt", {times_to_run}, is an integer, but it is either < 1 or > 20, 
so is interpreted as an extra argument for the "{BASIC_PYTEST_COMMAND}" command"""
                basic_logger.info(explain_str)
        except ValueError:
            pass
    # if we get here we are running the command once only
    extra_args_str = ' '.join(sys.argv[1:])
    run_command(extra_args_str)

def run_command(extra_args_str):
    """
NB if you capture the output you don't get things in colour (in W10 at least)
... but not capturing the output means that we can't find out (programmatically) what caused the "process error"
... however, an error message will be printed to the console, but it appears impossible to examine that in the program!
    """
    try:
        completed_process = subprocess.run(f'{BASIC_PYTEST_COMMAND} {extra_args_str}', encoding='utf-8')
    except BaseException as e:
        basic_logger.exception(f'+++ run was |{BASIC_PYTEST_COMMAND} {extra_args_str}|\ne {e}\ndir {dir(e)}')
        return False
    if completed_process.returncode > 1: # 0 for all tests green, 1 if one or more pytest fails/errors
        # we are not capturing the output, so completed_process.stdout == None and completed_process.stderr == None
        error_msg = f"""FATAL. The process raised an error.
completed_process.returncode {completed_process.returncode}
run was |{BASIC_PYTEST_COMMAND} {extra_args_str}|\ncompleted_process {completed_process}
"""
        basic_logger.error(error_msg)
        return False
    return True


    
