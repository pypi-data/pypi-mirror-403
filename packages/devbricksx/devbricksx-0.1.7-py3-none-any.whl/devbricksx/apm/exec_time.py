import time

from devbricksx.development.log import info, debug

map_of_exec_time = {}


def call_with_execution_statistics(func, *args, **kwargs):
    start_time = time.time()
    ret = func(*args, **kwargs)
    end_time = time.time()
    execution_time = round(end_time - start_time)

    func_name = func.__name__

    debug(f"Execution time for [{func_name}]: {execution_time} seconds")
    if func_name in map_of_exec_time:
        old_execution_time = map_of_exec_time[func_name]
        map_of_exec_time[func_name] = (old_execution_time + execution_time) / 2
    else:
        map_of_exec_time[func_name] = execution_time
    debug(f"Execution time for [{func_name}]: avg. {map_of_exec_time[func_name]} seconds")

    return ret


def print_statistics():
    for function_name, execution_time in map_of_exec_time.items():
        info("[{}]: {} seconds".format(function_name, execution_time))
