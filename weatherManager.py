import json
import socketpool
import wifi

CONFIG_FILE = "/location_config.txt"
WEATHER_HOST = "api.open-meteo.com"
WEATHER_PORT = 80


def _default_config():
    return {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone_offset": -4,
        "timezone": "US/Eastern",
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
                if key == "latitude":
                    config["latitude"] = float(value)
                elif key == "longitude":
                    config["longitude"] = float(value)
                elif key == "timezone_offset":
                    config["timezone_offset"] = int(value)
                elif key == "timezone":
                    config["timezone"] = value
    except OSError:
        saveConfig(config)
    except ValueError as error:
        print("Location config error:", error)
    return config


def saveConfig(config):
    try:
        with open(CONFIG_FILE, "w") as file:
            file.write("latitude=%s\n" % config["latitude"])
            file.write("longitude=%s\n" % config["longitude"])
            file.write("timezone_offset=%d\n" % config["timezone_offset"])
            file.write("timezone=%s\n" % config["timezone"])
    except OSError as error:
        print("Location config not saved:", error)


def _httpGet(host, path):
    pool = socketpool.SocketPool(wifi.radio)
    address = pool.getaddrinfo(host, WEATHER_PORT)[0][-1]
    socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    socket.settimeout(10)
    try:
        socket.connect(address)
        request = (
            "GET " + path + " HTTP/1.0\r\n"
            "Host: " + host + "\r\n"
            "Connection: close\r\n\r\n"
        )
        socket.send(request.encode("utf-8"))
        chunks = []
        buffer = bytearray(256)
        while True:
            count = socket.recv_into(buffer)
            if count <= 0:
                break
            chunks.append(bytes(buffer[:count]))
    finally:
        socket.close()
    return b"".join(chunks).decode("utf-8")


def _weatherKindFromCode(code):
    if code == 0:
        return "sun"
    if code == 1 or code == 2 or code == 3 or code == 45 or code == 48:
        return "cloud"
    if 51 <= code <= 67 or 80 <= code <= 82 or 95 <= code <= 99:
        return "rain"
    if 71 <= code <= 77 or 85 <= code <= 86:
        return "cloud"
    return "cloud"


def fetchWeather(config):
    if not wifi.radio.connected:
        return "none"

    path = (
        "/v1/forecast?latitude=%s&longitude=%s&current=weather_code&forecast_days=1"
        % (config["latitude"], config["longitude"])
    )
    try:
        response = _httpGet(WEATHER_HOST, path)
        bodyStart = response.find("\r\n\r\n")
        if bodyStart >= 0:
            response = response[bodyStart + 4 :]
        data = json.loads(response)
        code = int(data["current"]["weather_code"])
        return _weatherKindFromCode(code)
    except Exception as error:
        print("Weather fetch failed:", error)
        return "none"
