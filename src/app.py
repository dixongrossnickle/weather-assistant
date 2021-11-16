#!/usr/bin/python3.10
import sys
from weather import *

HELP_MESSAGE = "> python weather.py <arg>\nValid args:"
VALID_ARGS = ['hourly', 'nightly', ]
for arg in VALID_ARGS:
    HELP_MESSAGE += ('\n--' + arg)


def main(argv: list[str]):
    if len(argv) != 1:
        print(f"ERROR: 1 argument {'permitted' if len(argv) else 'required'}.\n" + HELP_MESSAGE)
        sys.exit(2)

    arg = argv[0].removeprefix('--')
    if arg not in VALID_ARGS:
        print(f'INVALID ARGUMENT: {arg}\n' + HELP_MESSAGE)
        sys.exit(2)

    wa = WeatherAssistant()
    if arg == 'hourly':
        notification = wa.hourly_check()
    elif arg == 'nightly':
        notification = wa.nightly_check()

    if notification != '':
        wa.send_sms(notification)


if __name__ == "__main__":
    main(sys.argv[1:])
