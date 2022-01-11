# weather-assistant

## Overview

I created this application to periodically check the weather forecast and send me notifications. It is executed regularly by cron, which runs a [shell script](https://github.com/dixongrossnickle/weather-assistant/blob/main/examples/shell_script.sh) that activates the Python virtual environment and runs the [main Python script](https://github.com/dixongrossnickle/weather-assistant/blob/main/src/run.py).

Python version: 3.10.1

---

## 3rd-party APIs

Weather forecast: [AccuWeather](https://developer.accuweather.com/)  
SMS gateway: [Twilio](https://www.twilio.com/)