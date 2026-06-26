# Project Rules

- The microcontroller board used in this project is an **ESP32-C3**. Always assume/use this board type for compilation, wiring, library usage, and deployment instructions.
- **USB CDC on Boot** must be set to **"Enabled"** in Arduino IDE settings (under Tools) to ensure serial output is sent to the USB port instead of physical UART pins.
- Always verify that the WLAN configuration (`ssid` and `password` variables) in the code is updated with active credentials before deployment to prevent the chip from overheating in an infinite connection loop.
