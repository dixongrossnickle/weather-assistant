import os
import requests
from collections import namedtuple
from datetime import datetime
from twilio.rest import Client


def location_key_search(api_key: str, query_str: str) -> str:
    """Calls AccuWeather location search API using the given query string
    and returns the first result."""
    request_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {
        'q': query_str,
        'apikey': api_key
    }
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

    def check_range_for_precip(self, forecast: list[dict], rnge: int) -> list[RainyHour]:
        """Checks the given range of the hourly forecast for precipitation.
        Returns a list of RainyHours (tuples containing the time and % chance)."""
        rainy_hours = []
        for hour in forecast[:rnge]:
            if hour['PrecipitationProbability'] > 0:
                rainy_hours.append(
                    RainyHour(
                        datetime.fromisoformat(hour['DateTime']),
                        hour['PrecipitationProbability']
                    )
                )

        return rainy_hours

    def hourly_check(self) -> str:
        """Checks next 3 hours for precipitation. Returns a string containing
        a notification if one was triggered, and an empty string otherwise."""
        msg = ''
        forecast = self.get_forecast(12)
        rainy_hours = self.check_range_for_precip(forecast, 3)
        # If list isn't empty, rain expected; append to notification.
        if len(rainy_hours) > 0:
            msg = self.format_precip_msg(rainy_hours, msg)

        return msg

    def nightly_check(self) -> str:
        """Almost the same as hourly check, but checks next 12 hours for precipitation
        as well as nightly low temperature."""
        msg = ''
        forecast = self.get_forecast(12)
        rainy_hours = self.check_range_for_precip(forecast, 12)
        if len(rainy_hours) > 0:
            msg = self.format_precip_msg(rainy_hours, msg)
        # On nightly run, check low temp. for tank heater notification
        temps = [int(h['Temperature']['Value']) for h in forecast]
        low = min(temps)
        if low < 37:  # prepend to msg
            s = f'Low of {low} degrees tonight. Turn on your tank heaters!'
            s += '' if msg == '' else '\n\n'
            msg = s + msg

        return msg

    def format_precip_msg(self, rainy_hours: list[RainyHour], msg: str) -> str:
        """Appends the given list of RainyHours as formatted text to the given msg string."""
        msg += 'Precipitation expected:'
        for rh in rainy_hours:
            msg += ('\n' +
                    f"{rh.time.strftime('%-I:%M')}:".ljust(8) + f"{rh.pct}%")

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
