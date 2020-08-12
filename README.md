# smsUps
Application to read data from SMS BRASIL UPS


Before run you need to install:
   https://github.com/eclipse/paho.mqtt.python 


git clone https://github.com/dmslabsbr/smsUps.git
cd smsUps
python3 -m venv ./smsUps/
source ./bin/activate
pip3 install paho-mqtt
pip3 install pyserial


ls /dev/tty*

Achei /dev/ttyUSB0


nano secrets.ini

python3 smsUPS.py


install as service - Raspiberry

sudo cp smsUPS.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/smsUPS.service
sudo chmod +x /home/pi/smsUps/smsUPS.py
sudo systemctl daemon-reload
sudo systemctl enable smsUPS.service
sudo systemctl start smsUPS.service
sudo systemctl status smsUPS.service



Commands

Send json to /home/ups/cmd
{
   "cmd": "",
   "val": ""
}

{cmd: "T", val: ""}  - testa bateria por 10 segundos - sem retorno  - "T"
{cmd: "M", val: ""}  - # Liga/desliga beep   - sem retorno  "M"
{cmd: "C", val: ""} - Cancela Teste "C"  - Não cancela o "L"
{cmd: "RAW", val: ""} - Envia para o nobreak os dados em val
   ex: {
         "cmd": "RAW",
         "val": "49ffffffffbb0d"
       }
{cmd: "CMD", val: ""} - Envia para o nobreak os dados em val e completa com o checksum
   ex: {
         "cmd": "CMD",
         "val": "49ffffffff"
       }



secrets.ini file

You should create your own secrets.ini file. Like this:

[secrets]
MQTT_HOST = 192.168.50.21
MQTT_USER = your_mqqt_user
MQTT_PASS = your_mqqt_file

[config]
PORTA = /dev/tty.usbserial-1440
INTERVALO = 60
INTERVALO_HASS = 120
ENVIA_JSON = True
ENVIA_MUITOS = True
ENVIA_HASS = True
ECHO = True
MQTT_TOPIC = home/ups/cmd
MQTT_PUB = home/ups
MQTT_HASS = homeassistant
LOG_FILE = '/var/tmp/smsUPS.log'


[device]
UPS_NAME = SMS
UPS_ID = 01