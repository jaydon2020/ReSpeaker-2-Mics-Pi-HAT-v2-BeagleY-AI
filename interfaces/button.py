import gpiod
import time

gpio17 = gpiod.find_line('GPIO17')
gpio17.request(consumer='button_read',
                type=gpiod.LINE_REQ_DIR_IN,
                flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP) # Or PULL_DOWN / BIAS_DISABLE

while True:
    # Read the value of the button pin
    current_state = gpio17.get_value()

    if current_state == 0:
        # Button is pressed (assuming pull-up resistor)
        print("On")
    else:
        # Button is released (assuming pull-up resistor)
        print("Off")

    time.sleep(1)