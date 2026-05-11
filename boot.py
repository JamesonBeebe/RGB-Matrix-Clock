import board
import digitalio
import storage

# Hold MENU while powering up to make CIRCUITPY writable from the computer.
# Otherwise, the clock can write runtime files.
hostWritable = False

try:
    menuButton = digitalio.DigitalInOut(board.GP15)
    menuButton.direction = digitalio.Direction.INPUT
    menuButton.pull = digitalio.Pull.UP
    hostWritable = not menuButton.value
    menuButton.deinit()
except Exception:
    hostWritable = False

storage.remount("/", hostWritable)
