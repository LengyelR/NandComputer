import threading
import time


class Circuit:
    def __init__(self, clock_speed, device, *args):
        """
        :param clock_speed: tick per second (Hz)
        """
        self.clock_speed = clock_speed
        self.device = device(*args)
        self.thread = None
        self.is_on = False

    def power_on(self):
        self.is_on = True

        def _loop():
            while self.is_on:
                time.sleep(1 / self.clock_speed)
                self.device.step()

        self.thread = threading.Thread(target=_loop)
        self.thread.start()

    def power_off(self):
        self.is_on = False
        self.thread.join()
