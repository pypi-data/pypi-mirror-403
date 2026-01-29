from devbricksx.common.string_ops import to_trimmed_str
from devbricksx.development.log import debug

def retry_calls(func, max_retries, *args, **kwargs):
    for i in range(max_retries):
        debug("trying call func[{}] for {} time".format(func.__name__, i + 1))
        ret = func(*args, **kwargs)
        debug("ret of func[{}] for {} time: {}".format(func.__name__, i + 1,
                                                       to_trimmed_str(ret)))

        if ret is not None:
            return ret
