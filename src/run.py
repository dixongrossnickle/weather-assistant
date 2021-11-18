#!/usr/bin/python3.10
import sys
from weather import *

VALID_ARGS = ('hourly', 'nightly', )

HELP_MESSAGE = (">>> python run.py <arg>\nValid args:\n" +
                '\n'.join([f'--{arg}' for arg in VALID_ARGS]))


def main(argv: list[str]):
    # Check number of arguments
    if len(argv) != 1:
        print(f"Invalid Argument Count: 1 argument {'permitted' if len(argv) else 'required'}.",
              HELP_MESSAGE, sep='\n')
        sys.exit(2)
    # Parse & validate argument
    arg = argv[0].removeprefix('--')
    if arg not in VALID_ARGS:
        print(f"Invalid Argument: {arg}", HELP_MESSAGE, sep='\n')
        sys.exit(2)
    # Check the weather
    wa = WeatherAssistant()
    notification = wa.check_weather(arg)
    # Check notification; send if not empty
    if notification != '':
        wa.send_sms(notification)


if __name__ == "__main__":
    main(sys.argv[1:])
