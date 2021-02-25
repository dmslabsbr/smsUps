#!/usr/bin/with-contenv bashio
set +u

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

bashio::log.red "Exporting config data"

export MQTT_HOST=$(jq --raw-output '.MQTT_HOST' $CONFIG_PATH)
export MQTT_USER=$(jq --raw-output '.MQTT_USER' $CONFIG_PATH)
export MQTT_PASS=$(jq --raw-output '.MQTT_PASS' $CONFIG_PATH)
export SMSUPS_SERVER=$(jq --raw-output '.SMSUPS_SERVER' $CONFIG_PATH)
export SMSUPS_CLIENTE=$(jq --raw-output '.SMSUPS_CLIENTE' $CONFIG_PATH)
export PORTA=$(jq --raw-output '.PORTA' $CONFIG_PATH)
export SHUTDOWN_CMD=$(jq --raw-output '.SHUTDOWN_CMD' $CONFIG_PATH)
export SMSUPS_SERVER=$(jq --raw-output '.SMSUPS_SERVER' $CONFIG_PATH)
export UPS_NAME=$(jq --raw-output '.UPS_NAME' $CONFIG_PATH)
export UPS_ID=$(jq --raw-output '.UPS_ID' $CONFIG_PATH)


bashio::log.info "PATH: "
pwd

echo $MQTT_HOST
echo $TESTE
echo $CONFIG_PATH




bashio::log.info "secrets.ini exists?"

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

echo "SMS BRASIL UPS"
python3 ../smsUPS.py
echo "Run Webserver"
python3 -m http.server 8000