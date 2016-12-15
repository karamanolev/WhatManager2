import time


class Throttler(object):
    def __init__(self, num_requests, per_seconds):
        self.num_requests = num_requests
        self.per_seconds = per_seconds
        self.request_times = []

    def throttle_request(self):
        request_time = time.time()
        if len(self.request_times) >= self.num_requests:
            sleep_time = self.per_seconds - (request_time - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.request_times = self.request_times[1:]
        self.request_times.append(request_time)
