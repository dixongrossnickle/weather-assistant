# weather-assistant

## Overview

I created this application to periodically check the weather forecast and send me notifications. It is scheduled to be executed periodically by cron (see [crontab example](https://github.com/dixongrossnickle/weather-assistant/blob/main/example_scripts/crontab)). The [shell script](https://github.com/dixongrossnickle/weather-assistant/blob/main/example_scripts/exec) passes an argument that dictates the type of check to be run (hourly, nightly, etc.) to the [main Python script](https://github.com/dixongrossnickle/weather-assistant/blob/main/src/run.py).

---

## 3rd-party APIs

Weather forecast: [AccuWeather](https://developer.accuweather.com/)  
SMS gateway: [Twilio](https://www.twilio.com/)

---

**Requires Python 3.10** (implements [structural pattern matching](https://docs.python.org/3/whatsnew/3.10.html#summary-release-highlights))