CONFIG_FILE = "/wifi_config.txt"
DEFAULT_SSID = "CHANGE_ME_SSID"
DEFAULT_PASSWORD = "CHANGE_ME_PASSWORD"
MAX_SSID_LENGTH = 20
MAX_PASSWORD_LENGTH = 20
WIFI_CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_- .@#$%&*+=!?"

try:
    import wifi
except ImportError:
    wifi = None


wifiStatus = "OFF"


def _default_config():
    return {
        "enabled": True,
        "ssid": DEFAULT_SSID,
        "password": DEFAULT_PASSWORD,
    }


def loadConfig():
    config = _default_config()
    try:
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key == "enabled":
                    config["enabled"] = value == "1"
                elif key == "ssid":
                    config["ssid"] = value[:MAX_SSID_LENGTH]
                elif key == "password":
                    config["password"] = value[:MAX_PASSWORD_LENGTH]
    except OSError:
        saveConfig(config)
    return config


def saveConfig(config):
    try:
        with open(CONFIG_FILE, "w") as file:
            file.write("enabled=%d\n" % (1 if config["enabled"] else 0))
            file.write("ssid=%s\n" % config["ssid"][:MAX_SSID_LENGTH])
            file.write("password=%s\n" % config["password"][:MAX_PASSWORD_LENGTH])
    except OSError as error:
        print("WiFi config not saved:", error)


def wifiAvailable():
    return wifi is not None


def isConnected():
    if wifi is None:
        return False
    try:
        return wifi.radio.connected
    except Exception:
        return False


def connect(config):
    global wifiStatus
    if wifi is None:
        wifiStatus = "NO WIFI"
        return False
    if not config["enabled"]:
        wifiStatus = "OFF"
        return False
    if config["ssid"] == "" or config["ssid"] == DEFAULT_SSID:
        wifiStatus = "NO SSID"
        return False
    try:
        if wifi.radio.connected:
            wifi.radio.stop_station()
    except Exception:
        pass
    try:
        try:
            wifi.radio.connect(config["ssid"], config["password"], timeout=10)
        except TypeError:
            wifi.radio.connect(config["ssid"], config["password"])
        wifiStatus = "WIFI OK"
        return True
    except Exception as error:
        wifiStatus = "NO WIFI"
        print("WiFi connect failed:", error)
        return False


def changeCharacter(text, index, step, maxLength):
    if len(text) == 0:
        text = " "
    while len(text) <= index and len(text) < maxLength:
        text += " "
    if index >= len(text):
        index = len(text) - 1
    character = text[index]
    try:
        characterIndex = WIFI_CHARSET.index(character)
    except ValueError:
        characterIndex = 0
    characterIndex = (characterIndex + step) % len(WIFI_CHARSET)
    text = text[:index] + WIFI_CHARSET[characterIndex] + text[index + 1 :]
    return text.rstrip()
