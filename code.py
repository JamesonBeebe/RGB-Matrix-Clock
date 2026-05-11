# This example implements a simple two line scroller using
# Adafruit_CircuitPython_Display_Text. Each line has its own color
# and it is possible to modify the example to use other fonts and non-standard
# characters.

import adafruit_display_text.label
import adafruit_imageload
import barkManager
import board
import brightnessManager
import displayio
import framebufferio
import rgbmatrix
import terminalio
import time
import displaySubsystem
import keyInput
import ntpManager
import rtc
import weatherManager
import wifiManager
from dirver_buzzer import *
from dirver_lightSensor import *

MaxDays = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

KEY_MENU = 0
KEY_DOWN = 1
KEY_UP = 2

SPLASH_BITMAP = "/startup.bmp"
LOGO_BITMAP = "/logo.bmp"
SPLASH_SECONDS = 3
LOGO_X = 40
LOGO_Y = 18
WIFI_STATUS_X = 57
WIFI_STATUS_Y = 19
WEATHER_STATUS_X = 57
WEATHER_STATUS_Y = 26
NTP_SYNC_SECONDS = 21600
WEATHER_UPDATE_SECONDS = 1800
WIFI_RETRY_SECONDS = 60
WOOF_BEEP_PATTERN = (
    (0.08, 0.04),
    (0.08, 0.20),
    (0.08, 0.04),
    (0.08, 0.20),
)

beepFlag = 1
startBeepFlag = 0
beepCount = 0

autoLightFlag = 0
brightnessLevel = brightnessManager.loadLevel()

selectSettingOptions = 0
pageID = 0

timeSettingLabel = 0
timeTemp = [0, 0, 0]  # hour,min,sec
dateTemp = [0, 0, 0]  # year,mon,mday
wifiConfig = wifiManager.loadConfig()
locationConfig = weatherManager.loadConfig()
barkConfig = barkManager.loadConfig()
lastWifiCheck = 0
lastWifiRetry = 0
lastNtpSync = -NTP_SYNC_SECONDS
lastWeatherUpdate = -WEATHER_UPDATE_SECONDS
weatherKind = "none"


keyMenuValue = 0
keyDownValue = 0
keyUpValue = 0


# Lookup table for names of days (nicer printing).

bit_depth_value = 1
base_width = 64
base_height = 32
chain_across = 1
tile_down = 1
serpentine_value = True

width_value = base_width * chain_across
height_value = base_height * tile_down


# If there was a display before (protomatter, LCD, or E-paper), release it so
# we can create ours
displayio.release_displays()

# This next call creates the RGB Matrix object itself. It has the given width
# and height. bit_depth can range from 1 to 6; higher numbers allow more color
# shades to be displayed, but increase memory usage and slow down your Python
# code. If you just want to show primary colors plus black and white, use 1.
# Otherwise, try 3, 4 and 5 to see which effect you like best.
#
# These lines are for the Feather M4 Express. If you're using a different board,
# check the guide to find the pins and wiring diagrams for your board.
# If you have a matrix with a different width or height, change that too.
# If you have a 16x32 display, try with just a single line of text.

matrix = rgbmatrix.RGBMatrix(
    width=width_value,height=height_value,bit_depth=bit_depth_value,
    rgb_pins=[board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9],
    addr_pins=[board.GP10, board.GP16, board.GP18, board.GP20],
    clock_pin=board.GP11,latch_pin=board.GP12,output_enable_pin=board.GP13,
    tile=tile_down,serpentine=serpentine_value,
    doublebuffer=True,
)

# Associate the RGB matrix with a Display so that we can use displayio features
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)
display.rotation = 0
display.brightness = brightnessManager.levelToBrightness(brightnessLevel)


def setDisplayGroup(group):
    try:
        display.root_group = group
    except AttributeError:
        display.show(group)


line1 = adafruit_display_text.label.Label(terminalio.FONT, color=0x00DD00)


line2 = adafruit_display_text.label.Label(terminalio.FONT, color=0x00DDDD)


line3 = adafruit_display_text.label.Label(terminalio.FONT, color=0x0000DD)
line3.x = 12
line3.y = 56

line4 = adafruit_display_text.label.Label(terminalio.FONT, color=0x00DD00)

# Put each line of text into a Group, then show that group.
g = displayio.Group()
g.append(line1)
g.append(line2)
g.append(line3)
g.append(line4)

clockLogo = None
try:
    logoBitmap, logoPalette = adafruit_imageload.load(LOGO_BITMAP)
except Exception as error:
    print("Clock logo not shown:", error)
else:
    clockLogo = displayio.TileGrid(
        logoBitmap, pixel_shader=logoPalette, x=width_value, y=LOGO_Y
    )
    g.append(clockLogo)

wifiStatusBitmap = displayio.Bitmap(5, 5, 3)
wifiStatusPalette = displayio.Palette(3)
wifiStatusPalette[0] = 0x000000
wifiStatusPalette[1] = 0x00DD00
wifiStatusPalette[2] = 0xDD0000
wifiStatusPalette.make_transparent(0)
wifiStatusIcon = displayio.TileGrid(
    wifiStatusBitmap, pixel_shader=wifiStatusPalette, x=width_value, y=WIFI_STATUS_Y
)
g.append(wifiStatusIcon)

weatherStatusBitmap = displayio.Bitmap(5, 5, 4)
weatherStatusPalette = displayio.Palette(4)
weatherStatusPalette[0] = 0x000000
weatherStatusPalette[1] = 0xDDDD00
weatherStatusPalette[2] = 0xDDDDDD
weatherStatusPalette[3] = 0x0000DD
weatherStatusPalette.make_transparent(0)
weatherStatusIcon = displayio.TileGrid(
    weatherStatusBitmap,
    pixel_shader=weatherStatusPalette,
    x=width_value,
    y=WEATHER_STATUS_Y,
)
g.append(weatherStatusIcon)

setDisplayGroup(g)


def setClockLogoVisible(visible):
    if clockLogo is None:
        return
    if visible:
        clockLogo.x = LOGO_X
    else:
        clockLogo.x = width_value


def drawWifiStatusIcon(connected):
    wifiStatusBitmap.fill(0)
    if connected:
        color = 1
        wifiStatusBitmap[2, 0] = color
        wifiStatusBitmap[1, 1] = color
        wifiStatusBitmap[3, 1] = color
        wifiStatusBitmap[0, 3] = color
        wifiStatusBitmap[2, 3] = color
        wifiStatusBitmap[4, 3] = color
        wifiStatusBitmap[2, 4] = color
    else:
        color = 2
        for position in range(5):
            wifiStatusBitmap[position, position] = color
            wifiStatusBitmap[4 - position, position] = color


def setWifiStatusVisible(visible):
    if visible:
        wifiStatusIcon.x = WIFI_STATUS_X
    else:
        wifiStatusIcon.x = width_value


def updateWifiStatusIcon():
    drawWifiStatusIcon(wifiManager.isConnected())


def drawWeatherIcon(kind):
    weatherStatusBitmap.fill(0)
    if kind == "sun":
        # Yellow sun.
        weatherStatusBitmap[2, 0] = 1
        weatherStatusBitmap[1, 1] = 1
        weatherStatusBitmap[2, 2] = 1
        weatherStatusBitmap[3, 1] = 1
        weatherStatusBitmap[1, 2] = 1
        weatherStatusBitmap[3, 2] = 1
        weatherStatusBitmap[2, 3] = 1
    elif kind == "cloud":
        # White cloud.
        weatherStatusBitmap[2, 0] = 2
        weatherStatusBitmap[1, 1] = 2
        weatherStatusBitmap[2, 1] = 2
        weatherStatusBitmap[3, 1] = 2
        weatherStatusBitmap[0, 2] = 2
        weatherStatusBitmap[1, 2] = 2
        weatherStatusBitmap[2, 2] = 2
        weatherStatusBitmap[3, 2] = 2
        weatherStatusBitmap[4, 2] = 2
        weatherStatusBitmap[1, 3] = 2
        weatherStatusBitmap[2, 3] = 2
        weatherStatusBitmap[3, 3] = 2
    elif kind == "rain":
        # Blue raindrop.
        weatherStatusBitmap[2, 0] = 3
        weatherStatusBitmap[1, 1] = 3
        weatherStatusBitmap[2, 1] = 3
        weatherStatusBitmap[3, 1] = 3
        weatherStatusBitmap[1, 2] = 3
        weatherStatusBitmap[2, 2] = 3
        weatherStatusBitmap[3, 2] = 3
        weatherStatusBitmap[1, 3] = 3
        weatherStatusBitmap[2, 3] = 3
        weatherStatusBitmap[3, 3] = 3
        weatherStatusBitmap[2, 4] = 3


def setWeatherStatusVisible(visible):
    if visible:
        weatherStatusIcon.x = WEATHER_STATUS_X
    else:
        weatherStatusIcon.x = width_value


def syncDateTimeFromNtp():
    try:
        currentTime = ntpManager.getLocalTime(
            locationConfig["timezone_offset"], locationConfig["timezone"]
        )
        if currentTime is None:
            return False
        rtc.RTC().datetime = currentTime
        displaySubsystem.rtc.datetime = currentTime
        return True
    except Exception as error:
        print("NTP sync failed:", error)
        return False


def updateWeather():
    global weatherKind
    weatherKind = weatherManager.fetchWeather(locationConfig)
    drawWeatherIcon(weatherKind)


def handleWifiReconnect():
    if not wifiConfig["enabled"]:
        return
    if wifiManager.isConnected():
        return
    if wifiManager.connect(wifiConfig):
        updateWifiStatusIcon()
        syncDateTimeFromNtp()
        updateWeather()
    else:
        updateWifiStatusIcon()


def playWoofWoofBeep():
    global beepCount, startBeepFlag
    if beepFlag == 0:
        return

    beepCount = 0
    startBeepFlag = 0
    for on_time, off_time in WOOF_BEEP_PATTERN:
        BUZZERON()
        time.sleep(on_time)
        BUZZEROFF()
        time.sleep(off_time)


def showSplashBitmap(shouldBark=True):
    start_time = time.monotonic()
    splash_shown = False
    try:
        bitmap, palette = adafruit_imageload.load(SPLASH_BITMAP)
    except Exception as error:
        print("Splash BMP not shown:", error)
    else:
        splash_group = displayio.Group()
        x = max(0, (width_value - bitmap.width) // 2)
        y = max(0, (height_value - bitmap.height) // 2)
        splash_group.append(displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y))
        setDisplayGroup(splash_group)
        splash_shown = True

    if shouldBark:
        playWoofWoofBeep()
    if splash_shown:
        remaining_time = SPLASH_SECONDS - (time.monotonic() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
        setDisplayGroup(g)

keyInput.keyInit()

showSystem = displaySubsystem.DISPLAYSUBSYSTEM()
showSplashBitmap(barkConfig["enabled"])
lastSplashHour = displaySubsystem.rtc.datetime.tm_hour
wifiManager.connect(wifiConfig)
updateWifiStatusIcon()
if wifiManager.isConnected():
    syncDateTimeFromNtp()
    updateWeather()
    lastNtpSync = time.monotonic()
    lastWeatherUpdate = time.monotonic()


def checkLightSensor():
    if autoLightFlag == 1:
        lightSensorValue = get_voltage()
        if lightSensorValue > 2800:
            display.brightness = 0.0
        else:
            display.brightness = brightnessManager.levelToBrightness(brightnessLevel)
    else:
        display.brightness = brightnessManager.levelToBrightness(brightnessLevel)


def judgmentBuzzerSwitch():
    global startBeepFlag
    if beepFlag == 1 and startBeepFlag == 0:
        BUZZERON()
        startBeepFlag = 1


def isLeapYear(year):  # 判断是否为闰年
    if year % 4 == 0 and year % 100 != 0:
        return True
    if year % 400 == 0:
        return True
    return False


def getMaxDay(month, year):  # 获取月份的最大天数
    if month < 1 or month > 12:
        print("error month")
        return -1
    maxDay = MaxDays[month]
    # 判断2月天数
    if year != -1 and month == 2:
        if isLeapYear(year):
            maxDay += 1
    return maxDay


def keyMenuProcessingFunction():
    global pageID, timeSettingLabel
    if pageID == 2 and selectSettingOptions <= 1:
        timeSettingLabel += 1
        if timeSettingLabel > 2:
            timeSettingLabel = 0
    pageID += 1
    if pageID > 2:
        pageID = 2


def keyDownProcessingFunction():
    global selectSettingOptions, timeTemp, dateTemp, beepFlag, autoLightFlag, brightnessLevel
    if pageID == 1:
        selectSettingOptions -= 1
        if selectSettingOptions == -1:
            selectSettingOptions = 4
    if pageID == 2:
        if selectSettingOptions == 0:  # 选择列表为时间设置（0）
            # 对时间进行设置
            if timeSettingLabel == 0:
                timeTemp[0] -= 1
                if timeTemp[0] < 0:
                    timeTemp[0] = 23
            elif timeSettingLabel == 1:
                timeTemp[1] -= 1
                if timeTemp[1] < 0:
                    timeTemp[1] = 59
            else:
                timeTemp[2] -= 1
                if timeTemp[2] < 0:
                    timeTemp[2] = 59
        if selectSettingOptions == 1:  # 选择列表为日期设置（1）
            # 对日期进行设置
            if timeSettingLabel == 0:
                dateTemp[0] -= 1
                if dateTemp[0] < 2000:
                    dateTemp[0] = 2099
            elif timeSettingLabel == 1:
                dateTemp[1] -= 1
                if dateTemp[1] < 1:
                    dateTemp[1] = 12
            else:
                dateTemp[2] -= 1
                if dateTemp[2] < 1:
                    dateTemp[2] = getMaxDay(dateTemp[1], dateTemp[0])
        if selectSettingOptions == 2:  # 选择列表为蜂鸣设置（2）
            # 改变蜂鸣按键的开关
            if beepFlag:
                beepFlag = 0
            else:
                beepFlag = 1
        if selectSettingOptions == 3:  # 选择列表为自动亮度设置（3）
            # 改变自动亮度的开关
            if autoLightFlag:
                autoLightFlag = 0
            else:
                autoLightFlag = 1
        if selectSettingOptions == 4:
            brightnessLevel -= 1
            brightnessLevel = brightnessManager.clampLevel(brightnessLevel)
            display.brightness = brightnessManager.levelToBrightness(brightnessLevel)


def keyUpProcessingFunction():
    global selectSettingOptions, timeTemp, dateTemp, beepFlag, autoLightFlag, brightnessLevel
    if pageID == 1:
        selectSettingOptions += 1
        if selectSettingOptions == 5:
            selectSettingOptions = 0
    if pageID == 2:
        if selectSettingOptions == 0:  # 选择列表为时间设置（0）
            # 对时间进行设置
            if timeSettingLabel == 0:
                timeTemp[0] += 1
                if timeTemp[0] == 24:
                    timeTemp[0] = 0
            elif timeSettingLabel == 1:
                timeTemp[1] += 1
                if timeTemp[1] == 60:
                    timeTemp[1] = 0
            else:
                timeTemp[2] += 1
                if timeTemp[2] == 60:
                    timeTemp[2] = 0
        if selectSettingOptions == 1:  # 选择列表为日期设置（1）
            # 对日期进行设置
            if timeSettingLabel == 0:
                dateTemp[0] += 1
                if dateTemp[0] > 2099:
                    dateTemp[0] = 2000
            elif timeSettingLabel == 1:
                dateTemp[1] += 1
                if dateTemp[1] > 12:
                    dateTemp[1] = 1
            else:
                dateTemp[2] += 1
                if dateTemp[2] > getMaxDay(dateTemp[1], dateTemp[0]):
                    dateTemp[2] = 1
        if selectSettingOptions == 2:  # 选择列表为蜂鸣设置（2）
            # 改变蜂鸣按键的开关
            if beepFlag:
                beepFlag = 0
            else:
                beepFlag = 1
        if selectSettingOptions == 3:  # 选择列表为自动亮度设置（3）
            # 改变自动亮度的开关
            if autoLightFlag:
                autoLightFlag = 0
            else:
                autoLightFlag = 1
        if selectSettingOptions == 4:
            brightnessLevel += 1
            brightnessLevel = brightnessManager.clampLevel(brightnessLevel)
            display.brightness = brightnessManager.levelToBrightness(brightnessLevel)


def keyExitProcessingFunction():
    global pageID, timeSettingLabel
    if pageID == 2 and selectSettingOptions <= 1:  # 如果设置了时间或日期，退出时写入RTC
        showSystem.setDateTime(selectSettingOptions, dateTemp, timeTemp)
        timeSettingLabel = 0
    if pageID == 2 and selectSettingOptions == 4:
        brightnessManager.saveLevel(brightnessLevel)
    pageID -= 1
    if pageID < 0:
        pageID = 0


def keyProcessing(keyValue):
    global keyMenuValue, keyDownValue, keyUpValue, beepCount, startBeepFlag
    if keyValue == KEY_MENU:  # 判断按下了哪一个按键
        keyMenuValue += 1
    if keyValue == KEY_DOWN:
        keyDownValue += 1
    if keyValue == KEY_UP:
        keyUpValue += 1

    if startBeepFlag == 1:  # 有按键按下
        beepCount += 1
        if beepCount == 3:
            BUZZEROFF()
            beepCount = 0
            startBeepFlag = 0

    if keyMenuValue > 0 and keyMenuValue < 20 and keyValue == None:
        keyMenuProcessingFunction()
        judgmentBuzzerSwitch()
        keyMenuValue = 0
    elif keyMenuValue >= 20 and keyValue == None:
        keyMenuValue = 0

    if keyDownValue > 0 and keyDownValue < 20 and keyValue == None:
        keyDownProcessingFunction()
        judgmentBuzzerSwitch()
        keyDownValue = 0
    elif keyDownValue >= 20 and keyValue == None:
        keyDownValue = 0

    if keyUpValue > 0 and keyUpValue < 20 and keyValue == None:
        keyUpProcessingFunction()
        judgmentBuzzerSwitch()
        keyUpValue = 0
    elif keyUpValue >= 20 and keyValue == None:
        keyExitProcessingFunction()
        judgmentBuzzerSwitch()
        keyUpValue = 0


# matrix.deinit()

while True:
    checkLightSensor()
    key_value = keyInput.getKeyValue()
    keyProcessing(key_value)
    now = displaySubsystem.rtc.datetime
    if now.tm_min == 0 and now.tm_hour != lastSplashHour:
        showSplashBitmap(barkConfig["enabled"] and now.tm_hour in barkConfig["hours"])
        lastSplashHour = now.tm_hour
    if time.monotonic() - lastWifiCheck > 5:
        lastWifiCheck = time.monotonic()
        updateWifiStatusIcon()
    if time.monotonic() - lastWifiRetry > WIFI_RETRY_SECONDS:
        lastWifiRetry = time.monotonic()
        handleWifiReconnect()
    if wifiManager.isConnected() and time.monotonic() - lastNtpSync > NTP_SYNC_SECONDS:
        if syncDateTimeFromNtp():
            lastNtpSync = time.monotonic()
    if (
        wifiManager.isConnected()
        and time.monotonic() - lastWeatherUpdate > WEATHER_UPDATE_SECONDS
    ):
        updateWeather()
        lastWeatherUpdate = time.monotonic()
    setClockLogoVisible(pageID == 0)
    setWifiStatusVisible(pageID == 0)
    setWeatherStatusVisible(pageID == 0)
    if pageID == 0:
        showSystem.showDateTimePage(line1, line2, line3, line4)
    else:
        line4.text = ""
    if pageID == 1:
        line3.text = ""
        showSystem.showSetListPage(line1, line2, selectSettingOptions)
    if pageID == 2 and selectSettingOptions == 0:
        line1.text = ""
        showSystem.timeSettingPage(line2, line3, timeSettingLabel, timeTemp)
    if pageID == 2 and selectSettingOptions == 1:
        line1.text = ""
        showSystem.dateSettingPage(line2, line3, timeSettingLabel, dateTemp)
    if pageID == 2 and selectSettingOptions > 1 and selectSettingOptions < 4:
        line1.text = ""
        showSystem.onOffPage(
            line2, line3, selectSettingOptions, beepFlag, autoLightFlag
        )
    if pageID == 2 and selectSettingOptions == 4:
        line1.text = ""
        showSystem.brightnessPage(line2, line3, brightnessLevel)
