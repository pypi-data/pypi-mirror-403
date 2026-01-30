from digitalio import Direction, DigitalInOut
import board
from busio import SPI

class MCP3201:
    """
    Simple driver for the MCP3201 12-bit SPI ADC.

    Reads raw 12-bit ADC values over SPI from the MCP3201 chip.
    """

    def __init__(self,
        spi_bus: SPI       = SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI),
        cs: DigitalInOut   = DigitalInOut(board.CE0),
        ref_voltage: float = 3.3
    ):
        """
        Initialize the MCP3201 driver.

        Args:
            spi_bus (busio.SPI, optional): The SPI bus instance. Defaults to board SPI.
            cs (digitalio.DigitalInOut, optional): Chip select pin for MCP3201. Defaults to CE0.
            ref_voltage (float): Reference voltage for ADC conversion. Defaults to 3.3V.
        """
        self.spi_bus      = spi_bus
        self.cs           = cs
        self.cs.direction = Direction.OUTPUT
        self.cs.value     = True  # Chip select inactive (high)
        self.ref_voltage  = ref_voltage


    def read(self) -> int:
        """
        Perform a single 12-bit ADC reading from the MCP3201.

        Returns:
            int: Raw 12-bit ADC value (0-4095).
        """
        buf = bytearray(2)
        while not self.spi_bus.try_lock():
            pass
        try:
            self.cs.value = False  # Select device (active low)
            self.spi_bus.write_readinto(b'\x00\x00', buf)
            self.cs.value = True
        finally:
            self.spi_bus.unlock()

        word = (buf[0] << 8) | buf[1]
        return (word >> 1) & 0x0FFF  # 12-bit value


    def read_voltage(self) -> float:
        """
        Read the ADC and convert the raw value to voltage.

        Returns:
            float: Voltage corresponding to the ADC reading.
        """
        raw = self.read()
        return (raw / 4096) * self.ref_voltage
