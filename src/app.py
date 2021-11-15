#!/usr/bin/python3.10
import sys
from weather import *

HELP_MESSAGE = "> weather.py <arg>\nValid args:"
VALID_ARGS = ['hourly', 'nightly',]
for arg in VALID_ARGS:
    HELP_MESSAGE += ('\n--' + arg)


def main(argv: list[str]):
    if len(argv) == 0:
        print('INVALID COMMAND: 1 argument required.\n' + HELP_MESSAGE)
        sys.exit(2)
    arg = argv[0]
    match arg:
        case '--hourly':
            arg = 'h'
        case '--nightly':
            arg = 'n'
        case _:
            print('INVALID ARGUMENT\n'+HELP_MESSAGE)
            sys.exit(2)

    wa = WeatherAssistant()
    if arg == 'h':
        notification = wa.hourly_check()
        if notification != '':
            wa.send_sms(notification)
    
    elif arg == 'n':
        notification = wa.nightly_check()
        if notification != '':
            wa.send_sms(notification)


if __name__ == "__main__":
    main(sys.argv[1:])
