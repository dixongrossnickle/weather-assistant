import os
import requests
from collections import namedtuple
from datetime import datetime
from twilio.rest import Client


def location_key_search(api_key: str, query_str: str) -> str:
    """Calls AccuWeather location search API using the given query string
    and returns the first result."""
    request_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {'q': query_str, 'apikey': api_key}
    results = requests.get(url=request_url, params=params).json()

    return results[0]['Key']


def get_location_key(api_key: str, location_str: str | None) -> str:
    """If a string is passed, calls location_key_search and returns the first result.
    If None, returns the default location key from the environment."""
    if location_str is None:
        return os.environ['DEFAULT_LOCATION']
    else:
        return location_key_search(api_key, location_str)


RainyHour = namedtuple('RainyHour', ['time', 'pct'])


class WeatherAssistant:
    def __init__(self, location_str: str = None) -> None:
        #TODO: Improve docstring
        """A class with methods for periodic weather monitoring and notifications."""
        self.__api_key = os.environ['ACCUWEATHER_API_KEY']
        self.__account_id = os.environ['TWILIO_ACCOUNT_SID']
        self.__auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.__from = os.environ['FROM_PHONE_NUMBER']
        self.__to = os.environ['TO_PHONE_NUMBER']
        self.location_key = get_location_key(self.__api_key, location_str)

    def get_forecast(self, hours: int) -> list[dict]:
        """Returns the hourly forecast for the next n hours (hours must be 1 or 12)."""
        if hours not in (1, 12):
            raise ValueError("n must be 1 or 12.")
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/{hours}hour/{self.location_key}"
        params = {'apikey': self.__api_key}
        response = requests.get(url=request_url, params=params)

        return response.json()

    def check_for_precip(self, forecast: list[dict], hour_range: int) -> list[RainyHour]:
        """Checks the given range of the hourly forecast for precipitation.
        Returns a list of RainyHours (tuples containing the time and % chance)."""
        rainy_hours = []
        for hour in forecast[:hour_range]:
            if hour['PrecipitationProbability'] > 0:
                rainy_hours.append(
                    RainyHour(
                        datetime.fromisoformat(hour['DateTime']),
                        hour['PrecipitationProbability']
                    )
                )

        return rainy_hours

    def format_msg_precip(self, msg: str, rainy_hours: list[RainyHour]) -> str:
        """Appends the given list of RainyHours as formatted text to the given msg string."""
        msg += 'Precipitation expected:'
        for rh in rainy_hours:
            msg += ('\n' +
                    f"{rh.time.strftime('%-I:%M')}:".ljust(8) + f"{rh.pct}%")

        return msg

    def format_msg_low(self, msg: str, low: int) -> str:
        """Prepends a tank heater reminder to msg."""
        s = f'Low of {low} degrees tonight. Turn on your tank heaters!'
        s += '' if msg == '' else '\n\n'

        return s + msg

    def check_weather(self, check_type: str):
        """Takes the parsed (AND VALIDATED) command line argument, which determines
        what to check for. Returns a message if a notification was triggered, and
        an empty string otherwise."""
        msg = ''
        match check_type:
            case 'hourly':
                hrs = 3  # range of forecast to check
                check_low = False
            case 'nightly':
                hrs = 12
                check_low = True
            case _:
                raise ValueError(check_type)
        # Get forecast for next 12 hours
        forecast = self.get_forecast(12)
        # Check for rain
        rainy_hours = self.check_for_precip(forecast, hrs)
        if len(rainy_hours):
            msg = self.format_msg_precip(msg, rainy_hours)
        # If nightly, check low temp
        if check_low:
            low = min([int(h['Temperature']['Value']) for h in forecast])
            if low < 37:
                msg = self.format_msg_low(msg, low)

        return msg

    def send_sms(self, message: str) -> None:
        """Sends the given string as an SMS message through Twilio."""
        client = Client(self.__account_id, self.__auth_token)
        sms = client.messages.create(
            body=message,
            from_=self.__from,
            to=self.__to
        )
        # TODO: Better way to log message status
        print(f'Sent: {sms.date_created}')
