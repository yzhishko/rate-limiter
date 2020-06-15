import time
from abc import ABC, abstractmethod


class Timer(ABC):

    @abstractmethod
    def next_tick_in_ms(self) -> int:
        """
        :return: time in milliseconds from epoch
        """
        pass


class SystemTimer(Timer):

    """
    Generate system timestamp in milliseconds from epoch
    """

    def next_tick_in_ms(self) -> int:
        return int(round(time.time() * 1000))
