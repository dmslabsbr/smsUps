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
sudo systemctl stop smsUPS.service


Install as service - OSX

* run as current user
cp smsUPS_laucher.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/smsUPS_laucher.plist
launchctl start dmslabs.python.smsUPS
launchctl stop dmslabs.python.smsUPS
launchctl unload dmslabs.python.smsUPS
launchctl remove dmslabs.python.smsUPS
launchctl list | grep smsUPS
rm /var/tmp/smsUPS.*

* run as root
sudo cp smsUPS_laucher.plist  /Library/LaunchDaemons
sudo launchctl load /Library/LaunchDaemons/smsUPS_laucher.plist
sudo launchctl start dmslabs.python.smsUPS
sudo launchctl stop dmslabs.python.smsUPS
sudo launchctl unload dmslabs.python.smsUPS
sudo launchctl remove dmslabs.python.smsUPS
sudo launchctl list | grep smsUPS
sudo rm /var/tmp/smsUPS.*

Commands

Send json to /home/ups/cmd
{
   "cmd": "",
   "val": ""
}

{cmd: "T", val: ""}  - testa bateria por 10 segundos - sem retorno  - "T"

{cmd: "TN", val: ""}  - testa bateria por n segundos - sem retorno  - "T"
   ex: {
         "cmd": "TN",
         "val": 120
       }

{cmd: "M", val: ""}  - # Liga/desliga beep   - sem retorno  "M"
   ex: {
         "cmd": "M"
       }
{cmd: "C", val: ""} - Cancela Shutdown ou Reestore
   ex: {
         "cmd": "C"
       }
{cmd: "D", val: ""} - Cancela Testes
   ex: {
         "cmd": "D"
       }
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
{cmd: "SHUTDOWN", val: ""} - Envia sinal para desligar maquinas rodando os clientes.
   ex: {
         "cmd": "SHUTDOWN",
         "val": ""
       }



secrets.ini file

You should create your own secrets.ini file. Like this:

[secrets]
MQTT_HOST = 192.168.50.21
MQTT_USER = your_mqqt_user
MQTT_PASS = your_mqqt_file

[config]
PORTA = /dev/tty.usbserial-1470, /dev/tty.usbserial-1440, /dev/ttyUSB0
INTERVALO_MQTT = 60
INTERVALO_HASS = 600
INTERVALO_SERIAL = 3
ENVIA_JSON = True
ENVIA_MUITOS = True
ENVIA_HASS = True
ECHO = True
MQTT_TOPIC = home/ups/cmd
MQTT_PUB = home/ups
MQTT_HASS = homeassistant
SMSUPS_SERVER = True
SMSUPS_CLIENTE = True
LOG_FILE = '/var/tmp/smsUPS.log'
SHUTDOWN_CMD = '"shutdown /s /t 1", "sudo shutdown now", "systemctl poweroff", "sudo poweroff"'


[device]
UPS_NAME = SMS
UPS_ID = 01
UPS_BATERY_LEVEL = 60



** atualizar Rasbian

sudo systemctl stop smsUPS.service
sudo git reset --hard
sudo git pull
sudo git merge origin/master
sudo rm /var/tmp/smsUPS.*
sudo systemctl start smsUPS.service
sudo systemctl status smsUPS.service



Outros comandos para desligar o iMac (osx)
osascript -e 'tell app "System Events" to shut down'