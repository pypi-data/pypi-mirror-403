import threading

DEFAULT_TIMEOUT = 1.0


class ManagedThread(threading.Thread):
    _stop_event = None
    _timeout = DEFAULT_TIMEOUT

    def __init__(self, name, target, timeout=DEFAULT_TIMEOUT, args=(), kwargs={}):
        super(ManagedThread, self).__init__(name=name, target=target, args=args, kwargs=kwargs)
        self._stop_event = threading.Event()
        self._timeout = timeout

    def stop(self):
        self._stop_event.set()
        self.join(self._timeout)

    def stopped(self):
        return self._stop_event.is_set()
