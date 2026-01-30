import socket
import time
from threading import Thread

from pitechcar.hardware.pwm_controller import PwmController


def _ptc_check_connectivity() -> bool:
    """
    Attempts to open a socket to check internet access.

    Returns:
        bool: True if internet is reachable, False otherwise.
    """
    try:
        socket.setdefaulttimeout(2)
        socket.create_connection(("8.8.8.8", 53))
        return True
    except socket.error:
        return False


class PiTechCarWiFiMonitor(Thread):
    """
    Threaded class to monitor Wi-Fi connectivity.
    Controls two PWM channels on the PCA9685 to indicate
    connection status (online/offline).

    Channel 0: ON when connected
    Channel 1: ON when disconnected
    """

    def __init__(self, pwm_controller: PwmController):
        """
        Initializes the Wi-Fi monitor.

        Args:
            pwm_controller (PwmController): Shared PWM controller singleton.
        """
        super().__init__(daemon=True)
        self._pwm_controller = pwm_controller
        self._running = True


    def run(self) -> None:
        """
        Periodically checks internet connectivity and updates the LED status.
        """
        last_state = None

        try:
            while self._running:
                connected = _ptc_check_connectivity()

                if connected != last_state:
                    self._update_led_state(connected)
                    last_state = connected

                time.sleep(1)
        except Exception as e:
            print(f"[Error] Exception in {self.__class__.__name__}: {e}")
        finally:
            # Turn off LEDs when the thread stops
            self.__turn_off_all_leds()


    def stop(self) -> None:
        """
        Stop the monitoring thread gracefully.
        """
        self._running = False


    def _update_led_state(self, connected: bool) -> None:
        """
        Updates PWM output to indicate connectivity status.

        Args:
            connected (bool): Current internet connectivity state.
        """
        self._pwm_controller.set_duty_cycle(0, 0xFFFF if connected else 0x0000)
        self._pwm_controller.set_duty_cycle(1, 0x0000 if connected else 0xFFFF)


    def __turn_off_all_leds(self) -> None:
        """
        Turn off both WiFi indicator LEDs by setting PWM duty cycles to zero.
        """
        self._pwm_controller.set_duty_cycle(0, 0x0000)
        self._pwm_controller.set_duty_cycle(1, 0x0000)
