<img src="https://github.com/dmslabsbr/smsUps/raw/master/M3.jpeg" alt="" width="200" />

# smsUps
Application to read data from SMS BRASIL UPS.

Alredy tested on [Nobreak Manager III Senoidal](https://www.amazon.com.br/Nobreak-Senoidal-Usm1500Bi-SMS-27572/dp/B07GS5J88M/ref=sr_1_2?__mk_pt_BR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=2D7H3SMWYKEZ9&dchild=1&tag=dmslabs07-20) but it should work in another models.

I developed this program because the software that the SMS provides for the Linux system did not meet me, I took and made integration with [Home Assistant](https://www.home-assistant.io/) through an add-on.

But you can use the application without using the Home Assistant. You just need a machine that runs Python3.



<a href="https://www.buymeacoffee.com/dmslabs"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a pizza&emoji=🍕&slug=dmslabs&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=9S3JYKPHR3XQ6)
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1MAC9RBnPYT9ua1zsgvhwfRoASTBKr4QL8)](https://www.blockchain.com/btc/address/1MAC9RBnPYT9ua1zsgvhwfRoASTBKr4QL8)

<img alt="Lines of code" src="https://img.shields.io/tokei/lines/github/dmslabsbr/smsUps">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/dmslabsbr/smsUps">



# Instructions

<img align="center" src="https://github.com/dmslabsbr/smsUps/raw/master/hass.io.png" alt="" width="30" /> [Home Assistant add-on instructions](DOCS.md)

Before run you need to install:
   https://github.com/eclipse/paho.mqtt.python 


```bash
git clone https://github.com/dmslabsbr/smsUps.git
cd smsUps
python3 -m venv ./smsUps/
source ./bin/activate
pip3 install paho-mqtt
pip3 install pyserial
```

You also need to discover which port your No-break (UPS) is connected.

```bash
ls /dev/tty*
```

I found **/dev/ttyUSB0**

You also need you **MQTT Server** address, username and password.

After this you could use your favorite text editor to edit **secrets.ini** file.

I like to use **nano**.

```bash
nano secrets.ini
```

## 1 - First running and test

To run smsUPS app, you could use this command:
```bash
python3 smsUPS.py
```
If all goes well, you can go to the next step and install the app as a service.

## 2 - Install as a service

### a) Raspiberry OS or other Linux OS

```bash
sudo cp smsUPS.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/smsUPS.service
sudo chmod +x /home/pi/smsUps/smsUPS.py
sudo systemctl daemon-reload
sudo systemctl enable smsUPS.service
sudo systemctl start smsUPS.service
sudo systemctl status smsUPS.service
sudo systemctl stop smsUPS.service
```

### b) OSX - iMac

* run as current user
  
```bash
cp smsUPS_laucher.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/smsUPS_laucher.plist
launchctl start dmslabs.python.smsUPS
launchctl stop dmslabs.python.smsUPS
launchctl unload dmslabs.python.smsUPS
launchctl remove dmslabs.python.smsUPS
launchctl list | grep smsUPS
rm /var/tmp/smsUPS.*
```

* run as root
```bash
sudo cp smsUPS_laucher.plist  /Library/LaunchDaemons
sudo launchctl load /Library/LaunchDaemons/smsUPS_laucher.plist
sudo launchctl start dmslabs.python.smsUPS
sudo launchctl stop dmslabs.python.smsUPS
sudo launchctl unload /Library/LaunchDaemons/smsUPS_laucher.plist
sudo launchctl remove dmslabs.python.smsUPS
sudo launchctl list | grep smsUPS
sudo rm /var/tmp/smsUPS.*
```

## 2 - Commands

* Send json string by **MQTT** to **/home/ups/cmd**

```json
{
   "cmd": "",
   "val": ""
}
```

* `{cmd: "T", val: ""}`  - testa bateria por 10 segundos - sem retorno  - "T"
```json 
   {
      "cmd": "TN",
      "val": ""
   }
```

* `{cmd: "TN", val: ""}`  - testa bateria por n segundos - sem retorno  - "T"

```json 
   {
      "cmd": "TN",
      "val": 120
   }
```

* `{cmd: "M", val: ""}`  -  Liga/desliga beep   - sem retorno  "M"

```json
   {
      "cmd": "M"
   }
```

* `{cmd: "C", val: ""}` - Cancela Shutdown ou Reestore
  
```json
   {
   "cmd": "C"
   }
```

* `{cmd: "D", val: ""}` - Cancela Testes

```json
   {
      "cmd": "D"
   }
```

* `{cmd: "RAW", val: ""}` - Envia para o nobreak os dados em val
  
```json
   {
      "cmd": "RAW",
      "val": "49ffffffffbb0d"
   }
```

* `{cmd: "CMD", val: ""}` - Envia para o nobreak os dados em val e completa com o checksum
  
```json
   {
      "cmd": "CMD",
      "val": "49ffffffff"
   }
```

* `{cmd: "SHUTDOWN", val: ""}` - Envia sinal para desligar máquinas rodando os clientes.
  
```json
   {
      "cmd": "SHUTDOWN",
      "val": ""
   }
```

## 3 - CONFIG

You should create your own **secrets.ini** file. Like this:

```bash
[secrets]
MQTT_HOST = 192.168.50.21
MQTT_USER = your_mqqt_user
MQTT_PASS = your_mqqt_file

[config]
PORTA = /dev/tty.usbserial-1470, /dev/tty.usbserial-1440, /dev/ttyUSB0
INTERVALO_MQTT = 60
INTERVALO_HASS = 600
INTERVALO_SERIAL = 3
SERIAL_CHECK_ALWAYS = temperatureC, batterylevel, UpsOk, BateriaBaixa, BateriaEmUso
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

```

On an Apple iMac (OSX) you can try other commands to shut down the computer.

Put this in your configuration file.

```bash
osascript -e 'tell app "System Events" to shut down'
```

## 4 - Reload after config changes.

You must reload the configuration after config file changes.

### a) Raspiberry OS or other Linux OS


```bash
sudo systemctl stop smsUPS.service
sudo git reset --hard
sudo git pull
sudo git merge origin/master
sudo rm /var/tmp/smsUPS.*
sudo systemctl start smsUPS.service
sudo systemctl status smsUPS.service
```

### b) OSX - iMac

* run as current user

```bash
launchctl stop dmslabs.python.smsUPS
launchctl start dmslabs.python.smsUPS
launchctl unload dmslabs.python.smsUPS
launchctl load ~/Library/LaunchAgents/smsUPS_laucher.plist
launchctl start dmslabs.python.smsUPS
launchctl list | grep smsUPS
```

* run as root

```bash
sudo launchctl stop dmslabs.python.smsUPS
sudo launchctl start dmslabs.python.smsUPS
sudo launchctl unload dmslabs.python.smsUPS
launchctl load ~/Library/LaunchAgents/smsUPS_laucher.plist
launchctl start dmslabs.python.smsUPS
launchctl list | grep smsUPS
```


###  Other things:

switch.json
> Quando '#' na primeira letra do nome, não carrega.