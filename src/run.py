#!/usr/bin/python3.10
import sys
from weather import *

VALID_ARGS = ('daily', 'hourly', 'nightly', )

HELP_MESSAGE = (">>> python run.py <arg>\nValid args:\n" +
                '\n'.join(f'--{arg}' for arg in VALID_ARGS))


def main(argv: list[str]) -> None:
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
    # Execute weather check
    wa = WeatherAssistant()
    if arg == 'daily':
        wa.exec_daily()
    elif arg == 'hourly':
        wa.exec_hourly()
    elif arg == 'nightly':
        wa.exec_nightly()


if __name__ == "__main__":
    main(sys.argv[1:])
