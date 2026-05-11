CONFIG_FILE = "/brightness_config.txt"
DEFAULT_LEVEL = 3


def loadLevel():
    try:
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("level="):
                    return clampLevel(int(line[6:]))
    except OSError:
        saveLevel(DEFAULT_LEVEL)
    except ValueError as error:
        print("Brightness config error:", error)
    return DEFAULT_LEVEL


def saveLevel(level):
    try:
        with open(CONFIG_FILE, "w") as file:
            file.write("level=%d\n" % clampLevel(level))
    except OSError as error:
        print("Brightness config not saved:", error)


def clampLevel(level):
    if level < 1:
        return 1
    if level > 10:
        return 10
    return level


def levelToBrightness(level):
    return clampLevel(level) / 10
