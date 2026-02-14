import time


class RateLimiter:
    def __init__(self, delay_seconds):
        self.delay = delay_seconds
        self.last_request = 0

    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()
