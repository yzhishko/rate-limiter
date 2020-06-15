from rate_limiter.queue import Queue
from typing import Dict

from rate_limiter.timer import Timer, SystemTimer


class RequestsPerTick:

    """
    Container that holds tick number and number of request per tick
    """
    def __init__(self, tick: int, rc=0):
        self.__tick: int = tick
        self.__req_count: int = rc

    @property
    def tick(self) -> int:
        return self.__tick

    @tick.setter
    def tick(self, tick: int):
        self.__tick = tick

    @property
    def req_count(self) -> int:
        return self.__req_count

    @req_count.setter
    def req_count(self, rc: int):
        self.__req_count = rc


class RateTracker:

    """
    Contains a queue of all time interval buckets with a number of requests per bucket and time tick for the bucket
    """
    def __init__(self, rps: int, bucket_ms_interval):
        # Queue that will be used to perform sliding window algorithm
        self.__requests_buckets: Queue[RequestsPerTick] = Queue()
        # rps limit
        self.__rps: int = rps
        # track last second requests count
        self.__last_second_requests_cnt: int = 0
        # bucket width in milliseconds
        self.__bucket_ms_interval = bucket_ms_interval

    def out_of_limit(self, request_time) -> bool:
        """
        :param request_time: request time in milliseconds
        :return: if a requests per second limit was reached
        """
        self.__clear_expired(request_time)
        return self.__last_second_requests_cnt >= self.__rps

    def add_request(self, request_time):
        """
        register request in tracker
        :param request_time:
        """
        self.__clear_expired(request_time)
        cur_tick = self.__get_ms_interval_tick(request_time)
        # append/update bucket with tick and requests per bucket count. Updates happen in tail.
        if self.__requests_buckets.size == 0 or self.__requests_buckets.tail().tick != cur_tick:
            self.__requests_buckets.append(RequestsPerTick(cur_tick, 1))
        else:
            top = self.__requests_buckets.tail()
            top.req_count = top.req_count + 1
        # increment last second requests count
        self.__last_second_requests_cnt += 1

    def __clear_expired(self, request_time):
        """
        clean up outdated intervals in the queue
        :param request_time:
        :return:
        """
        last_valid_ms_tick = self.__get_ms_interval_tick(request_time - 1000)
        # all outdated intervals  are in the head of the queue
        while self.__requests_buckets.size > 0 and self.__requests_buckets.head().tick <= last_valid_ms_tick:
            req_per_tick = self.__requests_buckets.poll()
            # adjust last second requests count
            self.__last_second_requests_cnt -= req_per_tick.req_count

    def __get_ms_interval_tick(self, request_time) -> int:
        """
        :return: tick that identifies an interval bucket
        """
        return request_time // self.__bucket_ms_interval


class UnlimitedRateTracker(RateTracker):
    """
    No limits on request rates
    """
    def __init__(self):
        super(UnlimitedRateTracker, self).__init__(0, 0)

    def out_of_limit(self, request_time) -> bool:
        return False

    def add_request(self, request_time):
        pass


class RateLimiter:
    """
        Rate Limiter based on sliding window and time bucketing
    """

    def __init__(self, timer: Timer = SystemTimer(), bucket_ms_interval: int = 1):
        self.__timer = timer
        # global rate tracker
        self.__global_rate_tracker = UnlimitedRateTracker()
        # stores rate trackers per user
        self.__user_rate_trackers: Dict[int, RateTracker] = {}
        # width of time bucket
        self.__bucket_ms_interval = bucket_ms_interval

    def configure_global_limit(self, rps: int):
        """
        Configure global rate limits
        :param rps: requests per second
        """
        self.__global_rate_tracker = \
            UnlimitedRateTracker() if rps <= 0 else RateTracker(rps, self.__bucket_ms_interval)

    def configure_limit(self, user_id: int, rps: int):
        """
        Configure user rate limits
        :param rps: requests per second
        """
        self.__user_rate_trackers[user_id] = \
            UnlimitedRateTracker() if rps <= 0 else RateTracker(rps, self.__bucket_ms_interval)

    def process_request(self, user_id: int) -> bool:
        """
        Check if user may perform a request and didn't exceed rps
        :param user_id: user identifier
        :return: True if request can be performed
        """
        request_time = self.__timer.next_tick_in_ms() # get current time in milliseconds
        user_rate_tracker = self.__user_rate_trackers[user_id] if user_id in self.__user_rate_trackers else None
        # use user rate tracker if specified
        if user_rate_tracker:
            if not user_rate_tracker.out_of_limit(request_time):
                user_rate_tracker.add_request(request_time)
                # contribute to global rate limiter also
                self.__global_rate_tracker.add_request(request_time)
                return True
            else:
                return False
        if not self.__global_rate_tracker.out_of_limit(request_time):
            self.__global_rate_tracker.add_request(request_time)
            return True
        return False
