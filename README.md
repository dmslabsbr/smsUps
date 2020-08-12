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
