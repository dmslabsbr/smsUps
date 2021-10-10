#!/usr/bin/with-contenv bashio
set +u

bashio::log.green "Starting add-on container..."
date

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

bashio::log.red "Exporting config data"

#export MQTT_HOST=$(jq --raw-output '.MQTT_HOST' $CONFIG_PATH)
#export MQTT_USER=$(jq --raw-output '.MQTT_USER' $CONFIG_PATH)
#export MQTT_PASS=$(jq --raw-output '.MQTT_PASS' $CONFIG_PATH)
export SMSUPS_SERVER=$(jq --raw-output '.SMSUPS_SERVER' $CONFIG_PATH)
export SMSUPS_CLIENTE=$(jq --raw-output '.SMSUPS_CLIENTE' $CONFIG_PATH)
export PORTA=$(jq --raw-output '.PORTA' $CONFIG_PATH)
export SHUTDOWN_CMD=$(jq --raw-output '.SHUTDOWN_CMD' $CONFIG_PATH)
export SMSUPS_SERVER=$(jq --raw-output '.SMSUPS_SERVER' $CONFIG_PATH)
export UPS_NAME=$(jq --raw-output '.UPS_NAME' $CONFIG_PATH)
export UPS_ID=$(jq --raw-output '.UPS_ID' $CONFIG_PATH)
export SMSUPS_FULL_POWER=$(jq --raw-output '.SMSUPS_FULL_POWER' $CONFIG_PATH)
export USE_SECRETS=$(jq --raw-output '.USE_SECRETS' $CONFIG_PATH)
export allow_shutdown=$(jq --raw-output '.allow_shutdown' $CONFIG_PATH)
export Long_lived_access_token=$(jq --raw-output '.Long_lived_access_token' $CONFIG_PATH)

bashio::log.blue "Getting mqqt data..."

export MQTT_HOST=$(bashio::services mqtt "host")
export MQTT_USER=$(bashio::services mqtt "username")
export MQTT_PASS=$(bashio::services mqtt "password")

export DEVELOPERS_MODE=$(jq --raw-output '.DEVELOPERS_MODE' $CONFIG_PATH)

ls * -la
pwd
bashio::log.green "Copying html templates..."
mkdir -p /data/templates
cp /*.html /data/templates
ls -la /data/templates

bashio::log.blue "PATH: "
pwd

bashio::log.green MQTT_HOST - $MQTT_HOST
bashio::log.green MQTT_PASS - $MQTT_PASS


if [ -e "secrets.ini" ]; then
    bashio::log.info "secrets.ini exists!"
fi

if [ -e "/data/secrets.ini" ]; then
    bashio::log.info "/data/secrets.ini exists!"
else
    bashio::log.info "/data/secrets.ini not exists!"
    if [ -e "/secrets.ini" ]; then
        bashio::log.info "Copying..."
        cp /secrets.ini /data 
    fi    
fi

bashio::log.blue "SMS BRASIL UPS - dmslabs"
python3 ../smsUPS.py
echo "Run Webserver"
python3 -m http.server 8000