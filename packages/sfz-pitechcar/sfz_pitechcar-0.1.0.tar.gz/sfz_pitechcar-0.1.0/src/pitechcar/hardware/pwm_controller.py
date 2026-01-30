from threading import Lock
import board
import busio
import time

from adafruit_motor.servo import Servo
from adafruit_pca9685 import PCA9685


class PwmController:
    """
    Basic singleton PWM controller hub.
    """

    _instance = None

    # -----------------------
    # Servo configuration
    # -----------------------
    SERVO_MIN = 50.0
    SERVO_MAX = 130.0
    SERVO_CENTER = 90.0
    SERVO_RETRIES = 3

    # -----------------------
    # Singleton logic
    # -----------------------
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        address: int = 0x40,
        frequency: int = 100,
        servo_channel: int = 10,
    ) -> None:
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._lock = Lock()

        # -----------------------
        # I2C bus
        # -----------------------
        self._i2c = busio.I2C(board.SCL, board.SDA)

        # -----------------------
        # PWM controller
        # -----------------------
        self._pwm = PCA9685(self._i2c, address=address)
        with self._lock:
            self._pwm.frequency = frequency

        # -----------------------
        # Servo
        # -----------------------
        self._servo = Servo(self._pwm.channels[servo_channel])
        self.center_servo()

    # =====================================================
    # Servo control
    # =====================================================
    def set_servo_angle(self, angle: float) -> None:
        """
        Set servo angle safely within min/max range.
        """
        safe_angle = max(self.SERVO_MIN, min(angle, self.SERVO_MAX))
        for _ in range(self.SERVO_RETRIES):
            try:
                with self._lock:
                    self._servo.angle = safe_angle
                return
            except OSError:
                time.sleep(0.05)
        print(f"[Warning] Failed to set servo angle: {safe_angle}")

    def center_servo(self) -> None:
        """Center the servo."""
        self.set_servo_angle(self.SERVO_CENTER)

    # =====================================================
    # PWM helpers
    # =====================================================
    def set_duty_cycle(self, channel: int, duty_cycle: int) -> None:
        """
        Safely set PWM channel duty cycle (0-65535).
        """
        duty_cycle = max(0, min(duty_cycle, 0xFFFF))
        with self._lock:
            self._pwm.channels[channel].duty_cycle = duty_cycle

    # =====================================================
    # Shutdown
    # =====================================================
    def deinit(self) -> None:
        """Safely deinitialize PWM and I2C, reset singleton."""
        try:
            self._pwm.deinit()
        finally:
            self._i2c.deinit()
        self._initialized = False
        PwmController._instance = None
