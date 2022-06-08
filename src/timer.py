import time

class Timer:
    @staticmethod
    def __ns_to_s(ns: int) -> int:
        return ns//1000000000

    def get_time_to_live(self):
        return self._time_to_live

    def get_starting_time(self):
        return self._starting_time

    def set_time_to_live(self, time_to_live: int):
        self._time_to_live = time_to_live

    def set_starting_time(self):
        self._starting_time = time.monotonic_ns()

    def check_timer(self) -> bool:
        return True if self.__ns_to_s(time.monotonic_ns() - self._starting_time) > self._time_to_live else False

    def time_left(self) -> int:
        return self._time_to_live - self.__ns_to_s(time.monotonic_ns() - self._starting_time)

global_timer = Timer()
