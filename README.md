# Smart Matrix Clock

CircuitPython clock for a Waveshare 64x32 RGB matrix kit with Raspberry Pi Pico W, buttons, DS3231 RTC, buzzer, light sensor, Wi-Fi, NTP time sync, and weather status.

## Main Features

- Shows large hour/minute clock on the left side of the matrix.
- Shows day and date on the right side.
- Shows the company logo in the bottom-right corner.
- Shows Wi-Fi status next to the logo.
- Shows a simple weather icon next to the Wi-Fi symbol:
  - yellow sun
  - white cloud
  - blue raindrop
- Shows the Jedi Dog splash image on startup and once every hour.
- Plays a short "woof woof" buzzer pattern on startup and at configured hourly bark times when beeps are enabled.
- Syncs date and time from NTP over Wi-Fi.
- Saves Wi-Fi settings across restarts.
- Gets current weather from Open-Meteo using latitude and longitude in `location_config.txt`.

## Buttons

The clock uses three buttons:

- `MENU`: enter/select/advance
- `DOWN`: move backward or decrease a value
- `UP`: move forward or increase a value
- Long-press `UP`: go back/exit

To return to the clock face from a menu, long-press `UP` until you are back at the clock.

## Settings Menu

Short-press `MENU` from the clock face to open the settings list.

Available settings:

- `TIME SET`: manually set hour, minute, second
- `DATE SET`: manually set year, month, day
- `BEEP SET`: enable or disable button beeps and the dog bark
- `autolight`: enable or disable automatic brightness
- `BRIGHT`: adjust display brightness from 1 to 10

Use `UP` and `DOWN` to move through the settings list. Press `MENU` to enter the selected setting.

## Setting Time And Date

In `TIME SET` or `DATE SET`:

- `MENU`: move to the next field
- `UP`: increase the selected field
- `DOWN`: decrease the selected field
- Long-press `UP`: save and go back

When Wi-Fi is connected, the clock will also sync time from NTP automatically.

## Wi-Fi Setup

Wi-Fi settings are stored in:

```text
wifi_config.txt
```

Example:

```text
enabled=1
ssid=YourWiFiName
password=YourWiFiPassword
```

Edit this file directly from your computer to configure Wi-Fi. Wi-Fi credentials are not edited from the clock menu.

The Wi-Fi status icon on the clock face shows:

- green Wi-Fi mark: connected
- red X: not connected

If Wi-Fi is enabled but disconnected, the clock retries the connection about every 60 seconds.

## Weather And Location

Weather settings are stored in:

```text
location_config.txt
```

For Sarasota, Florida:

```text
latitude=27.3364
longitude=-82.5307
timezone_offset=-4
timezone=US/Eastern
```

The `timezone=US/Eastern` setting automatically handles daylight saving time. `timezone_offset` is kept as a fallback.

Weather is fetched from Open-Meteo about every 30 minutes.

## Files On The Device

Important files:

- `code.py`: main program
- `displaySubsystem.py`: clock/menu display pages
- `wifiManager.py`: Wi-Fi connection and saved credentials
- `ntpManager.py`: NTP time sync and daylight saving logic
- `weatherManager.py`: weather fetch and weather-code mapping
- `wifi_config.txt`: saved Wi-Fi credentials
- `location_config.txt`: latitude, longitude, timezone
- `bark_config.txt`: hourly dog bark schedule
- `brightness_config.txt`: display brightness level from 1 to 10
- `startup.bmp`: Jedi Dog startup/hourly splash image
- `logo.bmp`: company logo
- `boot.py`: controls whether the Pico or computer can write to the filesystem

## Editing Files From A Computer

The clock normally owns write access to the filesystem while it runs. This lets runtime files be saved reliably.

To make the `CIRCUITPY` drive writable from your computer:

1. Unplug or reset the Pico W.
2. Hold the `MENU` button.
3. Plug in or reboot the Pico W while holding `MENU`.
4. The computer should now be able to edit files on `CIRCUITPY`.

If you are using Mu Editor, open the Serial console and press `Ctrl+C` to stop the running program and enter the REPL.

## Brightness

Brightness is stored in:

```text
brightness_config.txt
```

Default:

```text
level=3
```

Use the `BRIGHT` menu to adjust brightness from 1 to 10. Long-press `UP` to save and go back. If `autolight` is enabled, the light sensor can dim the display, but this brightness level is still used as the normal on-brightness.

## Dog Bark Schedule

Dog bark hours are stored in:

```text
bark_config.txt
```

Default:

```text
enabled=1
hours=12,17
```

Set `enabled=0` to disable the dog bark. The dog image still appears on startup and hourly.

Hours use 24-hour time, so `12` is noon and `17` is 5 PM. The startup bark plays when both `enabled=1` and `BEEP SET` is on, even if the current hour is not listed.
