# smsUps
Application to read data from SMS BRASIL UPS


You need to install https://github.com/eclipse/paho.mqtt.python 


sudo pip3 install pyserial

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