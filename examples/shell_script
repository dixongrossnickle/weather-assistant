#!/bin/bash
# This is an example of a script to activate the virtual environment
# and set the necessary environment variables. (executed by cron)

# cd into dir containing script, then step back into project dir
cd $(dirname $0)
cd ../

# Activate env
source env/bin/activate

# Set env variables
export ACCUWEATHER_API_KEY=''
export TWILIO_ACCOUNT_SID=''
export TWILIO_AUTH_TOKEN=''
export FROM_PHONE_NUMBER=''
export TO_PHONE_NUMBER=''
export DEFAULT_LOCATION=''

# Run Python script
python src/run.py $1

# Unset env variables
unset ACCUWEATHER_API_KEY
unset TWILIO_ACCOUNT_SID
unset TWILIO_AUTH_TOKEN
unset FROM_PHONE_NUMBER
unset TO_PHONE_NUMBER
unset DEFAULT_LOCATION

# Deactivate env
deactivate
