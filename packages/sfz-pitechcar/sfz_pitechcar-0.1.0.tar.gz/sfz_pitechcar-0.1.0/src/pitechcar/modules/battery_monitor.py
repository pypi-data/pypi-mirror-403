from enum import Enum
import time

from threading import Thread
from pitechcar.hardware.mcp3201 import MCP3201
from pitechcar.hardware.pwm_controller import PwmController


class PiTechCarBatteryMonitor(Thread):
    """
    Threaded class to monitor battery voltage using MCP3201 ADC.
    Updates three PWM channels on PCA9685 to indicate battery state:
    FULL, HALF, or EMPTY.
    """

    class BatteryState(Enum):
        INITIAL = -1
        EMPTY   = 0
        HALF    = 1
        FULL    = 2


    def __init__(self, pwm_controller: PwmController):
        """
        Initialize the battery monitor.

        Args:
            pwm_controller (PwmController): Shared PWM controller singleton.
        """
        super().__init__(daemon=True)
        self._pwm_controller = pwm_controller
        self._last_state     = self.BatteryState.INITIAL
        self._running        = True

        # Use default SPI and CE0 for MCP3201
        self._adc = MCP3201()  # SPI and CS default to board.SPI and CE0


    # =====================================================
    # Main thread loop
    # =====================================================
    def run(self) -> None:
        try:
            while self._running:
                # Read ADC and compute voltage (1:4 voltage divider).
                voltage = self._adc.read_voltage()
                battery_voltage = 4 * voltage

                if battery_voltage > 8.0:
                    new_state = self.BatteryState.FULL
                elif battery_voltage > 7.7:
                    new_state = self.BatteryState.HALF
                else:
                    new_state = self.BatteryState.EMPTY

                # Only update LEDs on state change.
                if new_state != self._last_state:
                    self.__update_led_state(new_state)
                    self._last_state = new_state

                time.sleep(1)
        except Exception as e:
            print(f"[Error] Exception in {self.__class__.__name__}: {e}")
        finally:
            self.__turn_off_all_leds()


    # =====================================================
    # Stop thread
    # =====================================================
    def stop(self) -> None:
        self._running = False


    # =====================================================
    # LED helpers
    # =====================================================
    def __update_led_state(self, state: BatteryState) -> None:
        """
        Update PWM outputs to indicate battery state.

        Channels:
            2 → FULL
            3 → HALF
            4 → EMPTY
        """
        self._pwm_controller.set_duty_cycle(2, 0xFFFF if state == self.BatteryState.FULL  else 0x0000)
        self._pwm_controller.set_duty_cycle(3, 0xFFFF if state == self.BatteryState.HALF  else 0x0000)
        self._pwm_controller.set_duty_cycle(4, 0xFFFF if state == self.BatteryState.EMPTY else 0x0000)


    def __turn_off_all_leds(self) -> None:
        """Turn off all battery indicator LEDs."""
        self._pwm_controller.set_duty_cycle(2, 0x0000)
        self._pwm_controller.set_duty_cycle(3, 0x0000)
        self._pwm_controller.set_duty_cycle(4, 0x0000)
