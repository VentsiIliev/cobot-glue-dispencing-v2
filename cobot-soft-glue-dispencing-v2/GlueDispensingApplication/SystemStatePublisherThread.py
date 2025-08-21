import threading
import time


class SystemStatePublisherThread(threading.Thread):
    def __init__(self, publish_state_func, interval=1.0):
        super().__init__(daemon=True)
        self.publish_state_func = publish_state_func
        self.interval = interval
        self._running = True

    def run(self):
        while self._running:
            self.publish_state_func()
            time.sleep(self.interval)

    def stop(self):
        self._running = False