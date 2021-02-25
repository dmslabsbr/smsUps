#!/usr/bin/with-contenv bashio
set +u

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

TESTE="/data/teste"

LOGINS=$(jq --raw-output ".logins | length" $CONFIG_PATH)
ANONYMOUS=$(jq --raw-output ".anonymous" $CONFIG_PATH)
KEYFILE=$(jq --raw-output ".keyfile" $CONFIG_PATH)
CERTFILE=$(jq --raw-output ".certfile" $CONFIG_PATH)
CAFILE=$(jq --raw-output --exit-status ".cafile | select (.!=null)" $CONFIG_PATH || echo "$CERTFILE")
REQUIRE_CERTIFICATE=$(jq --raw-output ".require_certificate" $CONFIG_PATH)
CUSTOMIZE_ACTIVE=$(jq --raw-output ".customize.active" $CONFIG_PATH)
LOGGING=$(bashio::info 'hassio.info.logging' '.logging')

bashio::log.info "PATH: "
pwd

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

#bashio::log.info "getting information..."
#MQTT_HOST=$(bashio::services mqtt "host")
#MQTT_USER=$(bashio::services mqtt "username")
#MQTT_PASSWORD=$(bashio::services mqtt "password")


echo "SMS BRASIL UPS"
python3 ../smsUPS.py
echo "Run Webserver"
python3 -m http.server 8000