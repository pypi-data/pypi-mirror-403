import time

from pitechcar.hardware.pihut_controller import PiHutController
from pitechcar.hardware.pwm_controller import PwmController

from pitechcar.modules.battery_monitor import PiTechCarBatteryMonitor
from pitechcar.hardware.motor_driver import PiTechCarMotorDriver
from pitechcar.modules.wifi_monitor import PiTechCarWiFiMonitor


class PiTechCar:
    """
    Main class representing the PiTech Car hardware.
    Initializes and manages shared resources and background threads.
    """

    def __init__(self) -> None:
        # -----------------------
        # PWM controller (servo + LEDs)
        # -----------------------
        self._pwm_controller = PwmController()  # singleton handles servo & LEDs

        # -----------------------
        # Motor driver (threaded)
        # -----------------------
        self._motor_driver = PiTechCarMotorDriver()
        self._motor_driver.start()

        # -----------------------
        # Wi-Fi monitor
        # -----------------------
        self._wifi_monitor = PiTechCarWiFiMonitor(pwm_controller=self._pwm_controller)
        self._wifi_monitor.start()

        # -----------------------
        # Battery monitor (default SPI/CE0)
        # -----------------------
        self._battery_monitor = PiTechCarBatteryMonitor(pwm_controller=self._pwm_controller)
        self._battery_monitor.start()

        # -----------------------
        # Game controller
        # -----------------------
        self.controller = PiHutController()


    # =====================================================
    # Main loop
    # =====================================================
    def run(self) -> None:
        """
        Main control loop: read controller input and drive motors/servo.
        """
        try:
            for state in self.controller.stream():
                # Motor speed (-1.0 to 1.0)
                self._motor_driver.set_speed(-state['ly'])

                # Steering angle (servo 50-130 via PWM controller)
                self._pwm_controller.set_servo_angle(90 - state['lx'] * 40)

                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Interrupted! Stopping car...")
            self.emergency_stop()
        finally:
            self.cleanup()
            print("Car shutdown complete.")


    # =====================================================
    # Emergency / shutdown
    # =====================================================
    def emergency_stop(self) -> None:
        """
        Immediately stop the motor and center the servo.
        """
        self._motor_driver.off()
        self._pwm_controller.center_servo()


    def cleanup(self) -> None:
        """
        Gracefully shut down the PiTech Car system.
        Stops all threads and releases hardware safely.
        """
        # Stop all background threads
        for thread in [self._wifi_monitor, self._battery_monitor, self._motor_driver]:
            thread.stop()
            thread.join()

        # Controller clean-up
        self.controller.close()

        # Deinitialize PWM controller
        try:
            self._pwm_controller.deinit()
        except Exception as e:
            print(f"[Warning] Failed to deinit PWM controller: {e}")

        # Allow hardware to settle
        time.sleep(0.5)
