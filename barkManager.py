CONFIG_FILE = "/bark_config.txt"
DEFAULT_BARK_HOURS = (12, 17)


def loadConfig():
    config = {
        "enabled": True,
        "hours": DEFAULT_BARK_HOURS,
    }
    try:
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("enabled="):
                    config["enabled"] = line[8:] == "1"
                if line.startswith("hours="):
                    hours = []
                    for value in line[6:].split(","):
                        value = value.strip()
                        if value == "":
                            continue
                        hour = int(value)
                        if 0 <= hour <= 23:
                            hours.append(hour)
                    config["hours"] = tuple(hours)
    except OSError:
        saveConfig(config)
    except ValueError as error:
        print("Bark config error:", error)
    return config


def loadBarkHours():
    return loadConfig()["hours"]


def saveConfig(config):
    try:
        with open(CONFIG_FILE, "w") as file:
            file.write("enabled=%d\n" % (1 if config["enabled"] else 0))
            file.write("hours=")
            first = True
            for hour in config["hours"]:
                if not first:
                    file.write(",")
                file.write("%d" % hour)
                first = False
            file.write("\n")
    except OSError as error:
        print("Bark config not saved:", error)
