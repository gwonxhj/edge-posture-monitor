import time
import gpiod

CHIP_PATH = "/dev/gpiochip0"
LINE_OFFSET = 18

chip = gpiod.Chip(CHIP_PATH)
line = chip.get_line(LINE_OFFSET)
line.request(
    consumer="test-buzzer",
    type=gpiod.LINE_REQ_DIR_OUT,
    default_vals=[0],
)

print("Start test")

try:
    while True:
        line.set_value(1)
        print("ON")
        time.sleep(0.3)

        line.set_value(0)
        print("OFF")
        time.sleep(2.0)
finally:
    line.set_value(0)
    line.release()
    chip.close()