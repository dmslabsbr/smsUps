import paho.mqtt.client as mqtt
import configparser
import time


# Config
MQTT_HOST = "mqtt.eclipse.org" 
MQTT_USERNAME  = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC  = "$SYS/#"
SECRETS = 'secrets.ini'

# VARS
Connected = False #global variable for the state of the connection


def get_secrets():
    ''' GET configuration data '''
    global MQTT_HOST
    global MQTT_PASSWORD
    global MQTT_USERNAME
    global MQTT_TOPIC
    try:
        from configparser import ConfigParser
        config = ConfigParser()
    except ImportError:
        from ConfigParser import ConfigParser  # ver. < 3.0
    try:
        config.read(SECRETS)
        MQTT_PASSWORD = config.get('secrets', 'MQTT_PASS')
        MQTT_USERNAME  = config.get('secrets', 'MQTT_USER')
        MQTT_TOPIC = config.get('secrets', 'MQTT_TOPIC')
        MQTT_HOST = config.get('secrets', 'MQTT_HOST')
    except:
        print ("defalt config")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc == 0:
        print ("Connected to " + MQTT_HOST)
        global Connected
        Connected = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(MQTT_TOPIC)
    else:
        print ("Connection failed")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))



get_secrets()

print ("pass: " + MQTT_PASSWORD)
print ("user: " + MQTT_USERNAME)


client = mqtt.Client()
client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, 1883, 60)

client.loop_start()  # start the loop

while not Connected:
    time.sleep(0.1)  # wait for connection

x = 0


while True:
    x = x + 1
    time.sleep(5)
    print (x)
    client.publish("python/test",x)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()