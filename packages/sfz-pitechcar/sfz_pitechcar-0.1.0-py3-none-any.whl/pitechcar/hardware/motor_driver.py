from threading import Thread
import time
import board
import digitalio
import pwmio


class PiTechCarMotorDriverException(Exception):
    """Custom exception for motor driver faults."""
    def __init__(self):
        super().__init__(
            "Motor driver error: Possible undervoltage, overcurrent, or overtemperature."
        )


class PiTechCarMotorDriver(Thread):
    """
    Threaded motor driver controller.
    Uses two PWM outputs to control a single motor's speed and direction.
    Monitors fault pin and raises exception on error.
    """

    def __init__(self):
        super().__init__(daemon=True)  # daemon thread so it stops with program

        # PWM outputs for motor control
        self._in1 = pwmio.PWMOut(board.D16, frequency=500, duty_cycle=0)
        self._in2 = pwmio.PWMOut(board.D26, frequency=500, duty_cycle=0)

        # Fault pin (active low)
        self._nfault           = digitalio.DigitalInOut(board.D6)
        self._nfault.direction = digitalio.Direction.INPUT
        self._nfault.pull      = digitalio.Pull.UP

        # Running flag for the thread loop
        self._running = True

        # Ensure motor is off at startup
        self.off()


    # =========================
    # Thread loop
    # =========================
    def run(self):
        """
        Thread loop: continuously monitor the fault pin and stop on error.
        Cleans up hardware automatically when the loop exits.
        """
        try:
            while self._running:
                try:
                    self._check_fault_state()
                except PiTechCarMotorDriverException as e:
                    # Handle motor fault without crashing the thread
                    print(f"[MotorDriver Fault] {e}")
                    self.off()  # stop the motor immediately
                    self.stop()  # stop the thread
                time.sleep(0.1)
        finally:
            self.cleanup()  # always release hardware when thread exits

    def stop(self):
        """Stop the thread gracefully."""
        self._running = False


    # =========================
    # Motor control
    # =========================
    def set_speed(self, speed: float) -> None:
        """
        Set motor speed and direction.

        Args:
            speed (float): -1.0 (full reverse) to 1.0 (full forward)
        """
        if speed == 0:
            self.off()
            return

        # Clamp to [-1, 1]
        speed = max(-1.0, min(1.0, speed))

        if speed < 0:
            # Reverse
            self._in2.duty_cycle = 0
            self._in1.duty_cycle = int(65535 * abs(speed))
        else:
            # Forward
            self._in1.duty_cycle = 0
            self._in2.duty_cycle = int(65535 * speed)


    def off(self):
        """Stop the motor immediately."""
        self._in1.duty_cycle = 0
        self._in2.duty_cycle = 0


    # =========================
    # Fault detection
    # =========================
    def _check_fault_state(self):
        if not self._nfault.value:
            raise PiTechCarMotorDriverException()


    # =========================
    # Cleanup
    # =========================
    def cleanup(self):
        """Release hardware resources safely."""
        self.off()
        try:
            self._in1.deinit()
            self._in2.deinit()
            self._nfault.deinit()
        except (AttributeError, RuntimeError):
            # Ignore errors if pins are already released
            pass
