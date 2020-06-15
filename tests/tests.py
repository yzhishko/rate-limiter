from rate_limiter.timer import Timer
from rate_limiter.rate_limiter import RateLimiter
from abc import ABC, abstractmethod


class MockTimer(Timer, ABC):

    def __init__(self):
        self.__idx = 0
        self.__times = self.get_times()

    def next_tick_in_ms(self):
        time = self.__times[self.__idx]
        self.__idx += 1
        return time

    @abstractmethod
    def get_times(self) -> []:
        """
        :return: Array of timestamps in milliseconds, that will be used to simulate request time
        """
        pass


def test_global_1_rps():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_global_limit(rps=1)

    assert rate_limiter.process_request(1)  # for 0 stamp
    assert not rate_limiter.process_request(2)  # 500
    assert rate_limiter.process_request(3)  # 1000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(4)  # 1001
    assert not rate_limiter.process_request(5)  # 1500
    assert rate_limiter.process_request(6)  # 2000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(7)  # 2001


def test_global_2_rps():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_global_limit(rps=2)

    assert rate_limiter.process_request(1)  # for 0 stamp
    assert rate_limiter.process_request(2)  # 500
    assert rate_limiter.process_request(3)  # 1000 this will pass because exactly 1 sec passed since request at 0
    # and only one request in between
    assert not rate_limiter.process_request(4)  # 1001
    assert rate_limiter.process_request(5)  # 1500 this will pass because exactly 1 sec passed since request at 500
    # and only one request in between
    assert rate_limiter.process_request(6)  # 2000
    assert not rate_limiter.process_request(7)  # 2001


def test_user_1_rps():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=1)

    assert rate_limiter.process_request(1)  # for 0 stamp
    assert not rate_limiter.process_request(1)  # 500
    assert rate_limiter.process_request(1)  # 1000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(1)  # 1001
    assert not rate_limiter.process_request(1)  # 1500
    assert rate_limiter.process_request(1)  # 2000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(1)  # 2001


def test_user_2_rps():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=2)

    assert rate_limiter.process_request(1)  # for 0 stamp
    assert rate_limiter.process_request(1)  # 500
    assert rate_limiter.process_request(1)  # 1000 this will pass because exactly 1 sec passed since request at 0
    # and only one request in between
    assert not rate_limiter.process_request(1)  # 1001
    assert rate_limiter.process_request(1)  # 1500 this will pass because exactly 1 sec passed since request at 500
    # and only one request in between
    assert rate_limiter.process_request(1)  # 2000
    assert not rate_limiter.process_request(1)  # 2001


def test_user_contributes_to_global_limit():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=1)
    rate_limiter.configure_global_limit(rps=1)

    # user 1 makes 1 request for in 1 second interval and contribute to global limit, second user can't execute during
    # the same interval
    assert rate_limiter.process_request(1)  # for 0 stamp user 1
    assert not rate_limiter.process_request(2)  # 500 since user 1 already made a request
    assert rate_limiter.process_request(1)  # 1000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(2)  # 1001 since user 1 just made a request
    assert not rate_limiter.process_request(1)  # 1500
    assert rate_limiter.process_request(1)  # 2000 this will pass because exactly 1 sec passed since last request
    assert not rate_limiter.process_request(2)  # 2001


def test_two_users_1_rps():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 1000, 1001, 1500, 2000, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=1)
    rate_limiter.configure_limit(user_id=2, rps=1)

    # because users have their own limits configured, they do not overlap
    assert rate_limiter.process_request(1)  # for 0 stamp and user 1
    assert rate_limiter.process_request(2)  # 500 it's OK, because it is user 2
    assert rate_limiter.process_request(1)  # 1000 will pass because exactly 1 sec passed since last request for user 1
    assert not rate_limiter.process_request(1)  # 1001 user 1 just made a request, won't pass
    assert rate_limiter.process_request(2)  # 1500 will pass because exactly 1 sec passed since last request for user 2
    assert not rate_limiter.process_request(2)  # 2000 user 2 made a request 500ms ago
    assert rate_limiter.process_request(1)  # 2001 will pass because more than 1 sec passed since a request for user 1


def test_user_1_rps_and_unlimited_for_others():
    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [0, 500, 550, 700, 800, 900, 999, 1001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=1)

    # user 1 has only limits configured, but others are unlimited
    assert rate_limiter.process_request(1)  # for 0 stamp and user 1
    assert rate_limiter.process_request(2)  # 500 other users unlimited
    assert rate_limiter.process_request(3)  # 550
    assert rate_limiter.process_request(4)  # 700
    assert rate_limiter.process_request(5)  # 800
    assert rate_limiter.process_request(6)  # 900
    assert not rate_limiter.process_request(1)  # 999 but user 1 already exceeded a limit
    assert rate_limiter.process_request(1)  # 1001 user 1 may execute, because 1 sec already passed since last success


def test_10_ms_bucket_interval():
    """
    This test expresses a drawback of designed rate limiter. Even the time interval between two requests with timestamps
    1007, 2001 is shorter than 1 second it still passes. The reason is we split our tracker by 10 milliseconds interval,
    so once we performed a bucketing the distance between two buckets would be exactly 1 second which is valid.
    The case won't pass for 1ms buckets. So, with 10ms wide bucket we produce 100 buckets, we may incorrectly identify
    a distance for half timestamps within a bucket, that gives us 0.5% error. With 1ms the error is 0.05%. We may
    decrease the error by decreasing the width of the bucket, but this will impact space and time complexity. Overall
    the number of buckets will not exceed 1000/[bucket width], so we can talk about effective constant time and space
    complexity.
    :return:
    """

    class TestTimer(MockTimer):

        def get_times(self) -> []:
            return [1007, 2001]

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=10)
    rate_limiter.configure_limit(user_id=1, rps=1)

    assert rate_limiter.process_request(1)  # for 1007 stamp
    assert rate_limiter.process_request(1)  # 2001

    rate_limiter = RateLimiter(TestTimer(), bucket_ms_interval=1)
    rate_limiter.configure_limit(user_id=1, rps=1)

    assert rate_limiter.process_request(1)  # for 1007 stamp
    assert not rate_limiter.process_request(1)  # 2001
