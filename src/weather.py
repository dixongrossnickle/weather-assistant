import os
import requests
from datetime import datetime
from twilio.rest import Client


def location_key_search(api_key: str, query_str: str) -> str:
    """Calls AccuWeather location search API and returns the first result."""
    request_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {'q': query_str, 'apikey': api_key}
    response = requests.get(url=request_url, params=params)

    return response.json()[0]['Key']


def has_rain(hour: dict, threshold: int = 10) -> bool:
    """Convenience function — checks if chance of rain for a given hour is above threshold."""
    return hour['PrecipitationProbability'] >= threshold


class WeatherAssistant:
    location_key = None

    def __init__(self, location_str: str = None):
        """
        A class with methods for periodic weather monitoring and notifications.

        If None is passed to init, the DEFAULT_LOCATION environment variable will be used
        as the location key. If a string is passed, location key is retrieved from
        AccuWeather's Locations search API (first search result).
        """
        try:
            self.__api_key = os.environ['ACCUWEATHER_API_KEY']
            self.__account_id = os.environ['TWILIO_ACCOUNT_SID']
            self.__auth_token = os.environ['TWILIO_AUTH_TOKEN']
            self.__from = os.environ['FROM_PHONE_NUMBER']
            self.__to = os.environ['TO_PHONE_NUMBER']
            if location_str is None:
                self.location_key = os.environ['DEFAULT_LOCATION']
            else:
                self.location_key = location_key_search(self.__api_key, location_str)

        except KeyError as e:
            env_var_error_msg = f"Env. variable {str(e)} not found. Make sure it has been set in the current environment."
            raise KeyError(env_var_error_msg) from e

    def get_forecast(self, n: int) -> list[dict]:
        """Returns the forecast for the next n hours (n must be 1 or 12)."""
        if n not in (1, 12):
            raise ValueError("n must be 1 or 12.")
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/{n}hour/{self.location_key}"
        params = {'apikey': self.__api_key}
        response = requests.get(url=request_url, params=params)

        return response.json()

    def check_for_rain(self, forecast: list[dict], hour_range: int = 12) -> str:
        """
        Checks the given range of the hourly forecast for precipitation.
        Returns an empty string if none expected, and a notification message otherwise.
        If range is omitted, defaults to the full range.
        """
        msg = ''
        for hour in forecast[:hour_range]:
            if has_rain(hour):
                time = datetime.fromisoformat(hour['DateTime']).strftime('%-I:%M')
                pc = hour['PrecipitationProbability']
                msg += ('\n' + f'{time}:'.ljust(8) + f'{pc}%')

        return 'Precipitation expected:' + msg if msg else msg

    def check_low_temp(self, forecast: list[dict], hour_range: int = 12) -> str:
        """
        Checks low temperature of the given range of the forecast. Returns
        a notification message if very cold, and an empty string otherwise.
        If range is omitted, defaults to the full range.
        """
        temps = [int(x['Temperature']['Value']) for x in forecast[:hour_range]]
        low = min(temps)
        if low <= 36:
            return f'Low of {low} degrees tonight. Turn on your tank heaters!'

        return ''

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

    def exec_hourly(self) -> None:
        """Executed hourly — checks the next 3 hours' precip. probability."""
        forecast = self.get_forecast(12)
        # Check 3 hrs ahead for rain
        msg = self.check_for_rain(forecast, 3)
        if msg:
            self.send_sms(msg)

    def exec_nightly(self) -> None:
        """Executed nightly — checks the next 12 hours' precip. probability,
        as well as the low temperature for the night."""
        forecast = self.get_forecast(12)
        # Check low temp
        msg = self.check_low_temp(forecast)
        if msg:
            msg += '\n\n'
        # Check rain thru night
        msg += self.check_for_rain(forecast)
        if msg:
            self.send_sms(msg)
