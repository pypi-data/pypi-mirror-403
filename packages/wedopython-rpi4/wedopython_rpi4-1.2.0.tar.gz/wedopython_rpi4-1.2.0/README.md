# wedopython_rpi4

Python library for controlling LEGO® WeDo 2.0 devices using Bluetooth Low Energy (BLE) via `gattlib`.  
This library is optimized for **Raspberry Pi 4** running Linux (e.g. Raspberry Pi OS Buster).

## Features

- Connect to LEGO WeDo 2.0 Smart Hub
- Control motors (start, stop, power, direction)
- Read distance sensor values
- Read tilt sensor values
- Play internal piezo sound tones
- Monitor battery level

## Requirements

- Raspberry Pi 4 with built-in Bluetooth or external BLE dongle
- Linux OS with BLE support (tested on Raspberry Pi OS Buster)
- Python 3.7 or higher
- `gattlib==0.20210616`

## Installation

> ⚠ It is **strongly recommended** to use a virtual environment for installing this library.

```bash
sudo apt update
sudo apt install libbluetooth-dev python3-dev

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install gattlib manually (may require build tools)
pip install gattlib==0.20210616

# Then install this library
pip install wedopython_rpi4
```

## Quick Example

```python
from wedo2python.app import WeDo2Python
device = WeDo2Python("04:EE:03:16:ED:1D")  # Replace with your WeDo Hub MAC
device.connect()

# Control motor on port B
device.motor_on("B")
device.set_motor_power("B", 70)

# Read tilt sensor on port A
device.tilt_sensor("A")
print("Tilt:", device.read_tilt_value())

# Disconnect
device.disconnect()
```

## Finding the MAC address

Run:

```bash
bluetoothctl
scan on
```

Look for a device named **LEGO Hub** or similar. The MAC address should look like: `04:EE:03:16:ED:1D`

## License

This project is licensed under the **GNU GPL v2 License**.  
You are free to use, modify, and distribute it under the terms of the license.

## Author

Developed by **Evangelia Anastasaki**  
Email: eveanast@gmail.com

## Notes

This library was originally developed for research and educational use.  
If you are looking for Raspberry Pi 5 support using `bleak`, see the companion project: [`wedo2py-rpi5`](https://pypi.org/project/wedo2py-rpi5)
