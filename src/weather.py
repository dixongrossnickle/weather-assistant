import os
import requests
from datetime import datetime
from twilio.rest import Client

# This file contains all of the code for interacting with AccuWeather API.
# Reference: https://developer.accuweather.com/apis


def location_key_search(query_str: str, api_key: str) -> str:
    """Calls AccuWeather location search API and returns the first result."""
    request_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {'q': query_str, 'apikey': api_key}
    response = requests.get(url=request_url, params=params)

    return response.json()[0]['Key']


class WeatherAssistant:
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
                self.location_key = location_key_search(location_str, self.__api_key)

        except KeyError as e:
            env_var_error_msg = f"Env. variable {str(e)} not found. Make sure it has been set in the current environment."
            raise KeyError(env_var_error_msg) from e

    def get_hourly_forecast(self, n: int, details: bool = False) -> list[dict]:
        """Returns a list of hourly forecasts for the next n hours (n must be either 1 or 12)."""
        if n not in (1, 12):
            raise ValueError("n must be 1 or 12.")
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/{n}hour/{self.location_key}"
        params = {'apikey': self.__api_key, 'details': details}
        response = requests.get(url=request_url, params=params)
        # See ../examples/http_responses/hourly
        return response.json()

    def get_daily_forecast(self, details: bool = False) -> dict:
        """Returns the daily forecast for one day."""
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{self.location_key}"
        params = {'apikey': self.__api_key, 'details': details}
        response = requests.get(url=request_url, params=params)
        # See ../examples/http_responses/daily
        return response.json()

    def rain_check(self, forecast: dict, hourly: bool) -> str:
        """Takes a day, night, or hour forecast (dict-like) as input. Returns a
        notification if precipitation is expected, and an empty string otherwise."""
        msg = ''
        if forecast['HasPrecipitation']:
            msg = "{} {} expected".format(
                forecast['PrecipitationIntensity'],
                forecast['PrecipitationType'].lower()
            )
            if hourly:
                msg += " over the next hour."
            else:
                msg += " for {} hours.".format(forecast['HoursOfPrecipitation'])

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

    def exec_hourly(self) -> None:
        """Executed hourly — checks the next hour for precipitation and sends a notification if expected."""
        forecast = self.get_hourly_forecast(1, details=True)[0]
        # Check precipitation
        msg = self.rain_check(forecast, hourly=True)
        if msg:
            self.send_sms(msg)

    def exec_daily(self) -> None:
        """Executed daily (in the morning) — generates a forecast summary and sends as a SMS message."""
        forecast = self.get_daily_forecast(details=True)['DailyForecasts'][0]
        msg = ["Good morning! Here's today's forecast:"]
        # Forecast description
        msg.append(forecast['Day']['LongPhrase'] + '.')
        # Check high temp
        high = int(forecast['Temperature']['Maximum']['Value'])
        msg.append(f'High of {high} degrees.')
        # Check for rain
        precip_msg = self.rain_check(forecast['Day'], hourly=False)
        if precip_msg:
            msg.append(precip_msg)

        self.send_sms(' '.join(msg))

    def exec_nightly(self) -> None:
        """Generates a nightly forecast summary and sends as a SMS message (similar to exec_daily)."""
        forecast = self.get_daily_forecast(details=True)['DailyForecasts'][0]
        msg = ["Here's tonight's forecast:"]
        # Description
        msg.append(forecast['Night']['LongPhrase'] + '.')
        # Check low temp; add tank heater reminder if cold
        low = int(forecast['Temperature']['Minimum']['Value'])
        temp_msg = f'Low of {low} degrees'
        if low <= 36:
            temp_msg += ' \u2014 turn on your tank heaters!'
        else:
            temp_msg += '.'
        msg.append(temp_msg)
        # Precipitation
        precip_msg = self.rain_check(forecast['Night'], hourly=False)
        if precip_msg:
            msg.append(precip_msg)

        self.send_sms(' '.join(msg))
