import os
import requests
from datetime import datetime
from twilio.rest import Client

# This file contains all of the code for interacting with AccuWeather API.
# Reference: https://developer.accuweather.com/apis


def location_key_search(api_key: str, query_str: str) -> str:
    """Calls AccuWeather location search API and returns the first result."""
    request_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {'q': query_str, 'apikey': api_key}
    response = requests.get(url=request_url, params=params)

    return response.json()[0]['Key']


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

    def exec_daily(self) -> None:
        """Executed daily (in the morning) — generates a forecast summary and sends as a SMS message."""
        forecast = self.get_daily_forecast()['DailyForecasts'][0]
        msg = "Today's forecast: "
        # Check high temp
        high = int(forecast['Temperature']['Maximum']['Value'])
        msg += f'High of {high} degrees. '
        # Forecast description
        msg += forecast['Day']['LongPhrase'] + '.'
        # Check for rain
        if forecast['Day']['HasPrecipitation']:
            msg += ('\n' + self.rain_check(forecast, time_of_day=1))

        self.send_sms(msg)

    def exec_hourly(self) -> None:
        """Executed hourly — checks the next 3 hours' precip. probability."""
        msg = ''
        forecast = self.get_hourly_forecast(12)
        # Check 3 hrs ahead for rain
        for hour in forecast[:3]:
            if hour['PrecipitationProbability'] >= 20:
                time = datetime.fromisoformat(hour['DateTime']).strftime('%-I:%M')
                pc = hour['PrecipitationProbability']
                msg += ('\n' + f'{time}:'.ljust(8) + f'{pc}%')

        if msg:
            msg = 'Precipitation expected:' + msg
            self.send_sms(msg)

    def exec_nightly(self) -> None:
        """Generates a nightly forecast summary and sends as a SMS message."""
        forecast = self.get_daily_forecast()['DailyForecasts'][0]
        msg = "Today's forecast: "
        # Check low temp;
        # add tank heater reminder if close to freezing
        low = int(forecast['Temperature']['Minimum']['Value'])
        msg += f'Low of {low} degrees'
        msg += ' \u2014 turn on your tank heaters! ' if low <= 36 else '. '
        # Description
        msg += forecast['Night']['LongPhrase'] + '.'
        # Check for precipitation
        if forecast['Night']['HasPrecipitation']:
            msg += ('\n' + self.rain_check(forecast, time_of_day=2))

        self.send_sms(msg)

    def get_hourly_forecast(self, n: int) -> list[dict]:
        """Returns the forecast for the next n hours (n must be 1 or 12)."""
        if n not in (1, 12):
            raise ValueError("n must be 1 or 12.")
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/{n}hour/{self.location_key}"
        params = {'apikey': self.__api_key}
        response = requests.get(url=request_url, params=params)

        return response.json()

    def get_daily_forecast(self) -> dict:
        """Returns the daily forecast for one day."""
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{self.location_key}"
        params = {'apikey': self.__api_key, 'details': True}
        response = requests.get(url=request_url, params=params)

        return response.json()

    def rain_check(self, daily_forecast: dict, time_of_day: int = 1) -> str:
        """Takes a daily forecast (dict-like) and the time of day (1: day, 2: night).
        Returns a message about the expected precipitation."""
        if time_of_day not in (1, 2):
            raise ValueError("time_of_day must be 1 (day) or 2 (night).")
        key = 'Day' if time_of_day == 1 else 'Night'
        n_hours = daily_forecast[key]['HoursOfPrecipitation']
        intensity = daily_forecast[key]['PrecipitationIntensity']
        kind = daily_forecast[key]['PrecipitationType'].lower()
        if kind == 'mixed':
            kind += ' precip.'

        return f'{intensity} {kind} expected for {n_hours} hours.'

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
