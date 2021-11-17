# weather-assistant

I created this application to periodically check the weather forecast and send me notifications. It is scheduled to be executed periodically by cron (see [crontab example](https://github.com/dixongrossnickle/weather-assistant/blob/main/example_scripts/crontab_example)). The [shell script](https://github.com/dixongrossnickle/weather-assistant/blob/main/example_scripts/script_example) passes an argument that dictates the type of check to be run (hourly, nightly, etc.) to the [main Python script](https://github.com/dixongrossnickle/weather-assistant/blob/main/src/run.py).

Python version: 3.10.0

## 3rd-party APIs

Weather forecast: [AccuWeather](https://developer.accuweather.com/)  
SMS gateway: [Twilio](https://www.twilio.com/)
