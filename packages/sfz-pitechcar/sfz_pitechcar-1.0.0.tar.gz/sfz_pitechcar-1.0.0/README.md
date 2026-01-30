# SFZ-PiTechCar (Python Package)
<table style="width: 100%;">
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/PiTechCar_Logo.png" alt="PiTechCar Logo" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Python-based software for controlling a Fischertechnik Maker Kit car via a custom-built PCB and
Raspberry Pi. Provides precise motor control (forward/backward) and steering via a servo. Supports
the official 8.4V Fischertechnik NiMH battery. <br /> <br />
Additional sensors can be connected using stemmaQT connectors and controlled with
CircuitPython-based libraries.
</p>
</td>
</tr>
</table>

---
## Required Hardware
<table style="width: 100%;">
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/ft_maker_kit_car.jpg" alt="Fischertechnik Maker Kit Car" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Fischertechnik Maker Kit Car <br /><br />
The base platform for the PiTech Car project, including chassis, wheels, motors, and
steering mechanism.
</p>
</td>
</tr>
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/ft_nimh_battery.png" alt="Fischertechnik NiMH battery" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Fischertechnik 8.4V NiMH Battery <br /><br />
Provides reliable power for the PiTech Car HAT+, motors, servo, and Raspberry Pi. Includes a 
standard charger.  
</p>
<p style="color: #A9CD61; font-weight: bold">
Note: Higher-power Raspberry Pi models may draw too much current, causing undervoltage 
warnings or preventing the Raspberry Pi from starting. It is recommended to use a 
Raspberry Pi 3 or Raspberry Pi 3A+.
</p>
</td>
</tr>
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/RaspberryPi_3A+.png" alt="Raspberry Pi 3A+" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Raspberry Pi 3A+ <br /><br />
Serves as the main controller for the car, running the Python software and handling
communication with the PiTech Car HAT+. Other Raspberry Pi models (e.g., 3B+, 4) are also 
compatible.
</p>
</td>
</tr>
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/SFZ_PiTech_Car_RPi_Hat_Top.png" alt="PiTech Car HAT+" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Custom-Built PiTech Car HAT+, Falko Schmidt, SFZ, 2025 <br /><br />
Handles motor control (forward/backward) and steering via servo, interfaces with the battery,
and provides stemmaQT connectors for additional sensors. Designed specifically to integrate
seamlessly with the Python control software and Raspberry Pi.
</p>
</td>
</tr>
<tr>
<td style="width: 250px;">
<img src="https://gitlab.com/F-Schmidt/sfz-pitechcar/-/raw/main/assets/rpi_controller.jpg" alt="Pi Hut Controller" width="250">
</td>
<td>
<p style="color: #A9CD61; font-weight: bold">
Pi Hut Controller (Remote Control) <br /><br />
Used to control the PiTech Car. Interfaces with the Raspberry Pi over USB, allowing the user
to drive, steer, and send commands remotely. Only the joysticks are used; the buttons can be
assigned for custom functionality.
</p>
</td>
</tr>
</table>


---


## Software Prerequisites

> ⚠️ This software only works on Raspberry Pi systems!

Create a virtual Python environment to isolate and manage all required software libraries:

```bash
python -m venv ftberry_python_venv
source ftberry_python_venv/bin/activate
```

The Python control software requires several CircuitPython libraries to interface with sensors.
On Raspberry Pi, these libraries rely on the **Blinka** compatibility layer from Adafruit. To 
install Blinka, run the following commands:

```bash
cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
```


---


## Software Installation

Before installing the software, make sure the Python virtual environment is activated.
Then install the software by running:

```bash
pip install sfz-pitechcar
```

All required dependencies listed below will be installed automatically.


---


## Pre-Usage
Before running the software, you need to identify and profile the controller you are using. The
Python library **ApproxEng Input** is used for this purpose. Follow the official profiling 
instructions here:

[ApproxEng Input Profiling Guide](https://approxeng.github.io/approxeng.input/profiling.html)

After profiling, move the generated YAML file into the correct directory as described in the 
documentation. Once this is done, your controller is ready for use with the PiTech Car software.


---


## Usage
After installing the package, the `pitechcar` command will be available in your shell.

### Basic usage
Start the car with the default (mixed) joystick control mode:

```bash
pitechcar
```

### Control modes
You can select how the joystick axes are mapped using the `--control` option:

* `mixed` (default):
  * Left joystick vertical axis controls speed
  * Right joystick horizontal axis controls steering
* `left_only`:
  * Left joystick controls both speed and steering
* `right_only`:
  * Right joystick controls both speed and steering

Example:

```bash
pitechcar --control left_only
```

### Stopping the car
Press **Ctrl+C** at any time to safely stop the motor and shut down all hardware components.


---


## Auto-start on boot
To have PiTechCar start automatically when the system boots, you can set it up
as a `systemd` service. First, create a small shell script that activates your
virtual environment and starts PiTechCar:

```bash
cd ~
nano pitechcar_controller.sh
```

Add the following content (adjust the virtual environment path and control mode if needed):

```bash
#!/bin/bash
source ~/ftberry_python_venv/bin/activate
pitechcar
```

Make the script executable:

```bash
chmod +x ~/pitechcar_controller.sh
```

Next, create a new service file:

```bash
sudo nano /etc/systemd/system/pitechcar_controller.service
```

Paste the following configuration and replace `USERNAME` with your actual Linux username:

```ini
[Unit]
Description=PiTechCar Controller
After=usb-devices.target
Wants=usb-devices.target

[Service]
Type=simple
User=USERNAME
WorkingDirectory=/home/USERNAME
ExecStart=/bin/bash /home/USERNAME/pitechcar_controller.sh
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable the service so it starts automatically on boot:

```bash
sudo systemctl enable pitechcar_controller.service
```

Once enabled, PiTechCar will launch automatically on every boot.
If you want to start it immediately, you can either reboot or
enter this command (without reboot):

```bash
sudo systemctl start pitechcar_controller.service
```


---


## Python Package Dependencies

> ℹ️ All dependencies listed here are automatically installed with the package.

* [ApproxEng Input 2.6.4 (Linux only)](https://pypi.org/project/approxeng.input/2.6.4/)<br />
  Provides joystick and controller input handling.

* [Adafruit Python Shell 1.11.1](https://pypi.org/project/adafruit-python-shell/1.11.1/)<br />
  Helps run Python scripts on the Raspberry Pi via the shell, required for Blinka.

* [Adafruit CircuitPython PCA9685 3.4.20](https://pypi.org/project/adafruit-circuitpython-pca9685/3.4.20/)<br />
  Controls PCA9685 PWM controllers.

* [Adafruit CircuitPython ServoKit 1.3.22](https://pypi.org/project/adafruit-circuitpython-servokit/1.3.22/)<br />
  Provides an easy interface to control multiple servos via ServoKit.

* [Adafruit CircuitPython MCP3xxx 1.5.0](https://pypi.org/project/adafruit-circuitpython-mcp3xxx/1.5.0/)<br />
  Reads analog sensors via MCP3008/MCP3208 ADC chips.


---


## Project Structure

```
sfz-pitechcar/
├── assets/              # Images and diagrams for README
├── scripts/             # Example scripts
│   └── run_car.py       # Main script to start the PiTech Car
├── src/pitechcar/       # Python package
│   ├── hardware/        # Low-level hardware modules (motors, sensors, battery)
│   └── modules/         # Higher-level control modules (motor, battery, WiFi)
├── README.md
├── pyproject.toml
```

---

## Contributing
Contributions are welcome! To contribute, please fork the repository, make your changes,
and submit a merge request. For major changes or feature additions, consider opening an
issue first to discuss your ideas.

---

## License
This project is licensed under the BSD-3-Clause License. © 2026 Falko Schmidt.
