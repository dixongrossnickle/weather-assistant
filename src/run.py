#!/usr/bin/python3.10
import sys
from weather import *

HELP_MESSAGE = ">>> python ~/src/run.py <arg>\nValid args:"
VALID_ARGS = ('hourly', 'nightly', )
for arg in VALID_ARGS:
    HELP_MESSAGE += ('\n--' + arg)


def main(argv: list[str]):
    # Check number of arguments
    if len(argv) != 1:
        print(
            f"Invalid Argument Count: 1 argument {'permitted' if len(argv) else 'required'}.\n"
            + HELP_MESSAGE)
        sys.exit(2)
    # Check argument
    arg = argv[0].removeprefix('--')
    if arg not in VALID_ARGS:
        print(f"Invalid Argument: {arg}\n" + HELP_MESSAGE)
        sys.exit(2)
    # Check the weather
    wa = WeatherAssistant()
    if arg == 'hourly':
        notification = wa.hourly_check()
    elif arg == 'nightly':
        notification = wa.nightly_check()
    # Check notification
    if notification != '':
        wa.send_sms(notification)


if __name__ == "__main__":
    main(sys.argv[1:])