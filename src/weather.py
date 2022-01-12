# This file contains all of the code for interacting with AccuWeather API.
# Reference: https://developer.accuweather.com/apis
import requests
from collections import namedtuple
from os import environ as OS_ENVIRON
from twilio.rest import Client

Location = namedtuple('Location', ['key', 'name'])


def location_key_search(api_key: str, **kwargs) -> Location:
    """Calls AccuWeather location search API using the given query string
    and returns the first result as a Location namedtuple."""
    if len(kwargs) != 1:
        raise TypeError('Function takes 1 keyword arg that specifies the type of search to perform.')
    for kw, arg in kwargs.items():
        kw, arg = kw, arg
    # Match URL to keyword
    if kw == 'text_search':
        request_url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
    elif kw == 'coord_search':
        request_url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
    else:
        raise TypeError(f"Valid keywords are: {', '.join('text_search', 'coord_search')}.")
    # Make request
    params = {'q': arg, 'apikey': api_key}
    response = requests.get(url=request_url, params=params)
    json = response.json()
    # If JSON is list, the text_search API was called; take the top result.
    if isinstance(json, list):
        result = json[0]
    # Otherwise, coord_search API was called (returns 1 result as dict)
    else:
        result = json

    return Location(result['Key'], result['LocalizedName'])


class WeatherAssistant:
    def __init__(self, location_string: str = None):
        """
        A class with methods for periodic weather monitoring and notifications.

        If a string is passed to init, location is retrieved from AccuWeather search API.
        If nothing is passed, location is set from environment variables.
        """
        try:
            self.__api_key = OS_ENVIRON['ACCUWEATHER_API_KEY']
            self.__account_id = OS_ENVIRON['TWILIO_ACCOUNT_SID']
            self.__auth_token = OS_ENVIRON['TWILIO_AUTH_TOKEN']
            self.__from = OS_ENVIRON['FROM_PHONE_NUMBER']
            self.__to = OS_ENVIRON['TO_PHONE_NUMBER']
            if location_string is None:
                self.location = location_key_search(self.__api_key, coord_search = OS_ENVIRON['DEFAULT_LOCATION'])
            else:
                self.location = location_key_search(self.__api_key, text_search = location_string)

        except KeyError as e:
            env_var_error_msg = f"Env. variable {str(e)} not found. Make sure it has been set in the current environment."
            raise KeyError(env_var_error_msg) from e

    def get_hourly_forecast(self, n: int, details: bool = False) -> list[dict]:
        """Returns a list of hourly forecasts for the next n hours (n must be either 1 or 12)."""
        if n not in (1, 12):
            raise ValueError("n must be 1 or 12.")
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/{n}hour/{self.location.key}"
        params = {'apikey': self.__api_key, 'details': details}
        response = requests.get(url=request_url, params=params)
        # JSON structure: ../examples/http_responses/hourly
        return response.json()

    def get_daily_forecast(self, details: bool = False) -> dict:
        """Returns the daily forecast for one day."""
        request_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{self.location.key}"
        params = {'apikey': self.__api_key, 'details': details}
        response = requests.get(url=request_url, params=params)
        # JSON structure: ../examples/http_responses/daily
        return response.json()

    def rain_check(self, forecast: dict, hourly: bool) -> str:
        """Takes a day/night/hour forecast (dict-like) as input. Returns a
        notification if precipitation is expected, and an empty string otherwise.
        The 'hourly' param dictates the wording of the returned notification."""
        msg = ''
        if forecast['HasPrecipitation']:
            msg = "{} {} expected".format(
                forecast['PrecipitationIntensity'],
                forecast['PrecipitationType'].lower()
            )
            if hourly:   # form entire msg for self.exec_hourly
                msg = f"{self.location.name.upper()}: " + msg
                msg += " over the next hour."
            else:        # part of a greater daily/nightly notification
                msg += f" for {forecast['HoursOfPrecipitation']} hours."

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
        msg = [f"Today's forecast for {self.location.name}:"]
        # Forecast description
        msg.append(forecast['Day']['LongPhrase'] + '.')
        # Check high temp
        high = int(forecast['Temperature']['Maximum']['Value'])
        msg.append(f'High of {high} degrees.')
        # Check for precipitation
        precip_msg = self.rain_check(forecast['Day'], hourly=False)
        if precip_msg:
            msg.append(precip_msg)

        self.send_sms(' '.join(msg))

    def exec_nightly(self) -> None:
        """Generates a nightly forecast summary and sends as a SMS message (similar to exec_daily)."""
        forecast = self.get_daily_forecast(details=True)['DailyForecasts'][0]
        msg = [f"Tonight's forecast for {self.location.name}:"]
        # Description
        msg.append(forecast['Night']['LongPhrase'] + '.')
        # Check low temp
        low = int(forecast['Temperature']['Minimum']['Value'])
        msg.append(f'Low of {low} degrees.')
        # Check precipitation
        precip_msg = self.rain_check(forecast['Night'], hourly=False)
        if precip_msg:
            msg.append(precip_msg)

        self.send_sms(' '.join(msg))
