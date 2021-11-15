# weather-assistant
A weather notification app written in Python.

I created this application to periodically check the weather forecast and send me notifications. It is scheduled to run hourly during the daytime, and once each evening, by cron. The main script (app.py) is passed an argument that dictates the type of check to be run (hourly, nightly, etc.).
