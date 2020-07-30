__author__ = 'dmslabs'

import serial
import time
import struct
import binascii
import os
import paho.mqtt.client as mqtt
import configparser
import json

# CONFIG
SECRETS = 'secrets.ini'
MQTT_HOST = "mqtt.eclipse.org" 
MQTT_USERNAME  = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC  = "$SYS/#"
MQTT_PUB = "home/ups"
PORTA = '/dev/tty.usbserial-1440' # '/dev/ttyUSB0'
INTERVALO = 5
ENVIA_JSON = True
ENVIA_MUITOS = True

# CONST
CR = '0D'

cmd =[None] * 20
respostaH = [None] * 18

cmd[1] = "51 ff ff ff ff b3 0d" # pega_dados "Q"
cmd[2] = "49 ff ff ff ff bb 0d" # retorna nome do no-break - :MNG3 1500 Bi1.2o  "I"
cmd[3] = "44 ff ff ff ff c0 0d" # para teste de bateria - sem retorno "D"
cmd[4] = "46 ff ff ff ff be 0d" # caracteristicas  "F" - ;EBiS115000 2460o
cmd[5] = "47 01 ff ff ff bb 0d" # ? "G"
cmd[6] = "4d ff ff ff ff b7 0d" # Liga/desliga beep   - sem retorno  "M"        
cmd[7] = "54 00 10 00 00 9c 0d" # testa bateria por 10 segundos - sem retorno  - "T"
cmd[8] = "54 00 64 00 00 48 0d" # t 1 minuto
cmd[9] = "54 00 c8 00 00 e4 0d" # t 2 minutos  
cmd[9] = "54 01 2c 00 00 7f 0d" # t 3 minutos  
cmd[9] = "54 03 84 00 00 25 0d" # t 9 minutios  
cmd[10]= "43 ff ff ff ff c1 0d" # Cancela Teste "C"       
cmd[11] = "" # teste bateria baixa "L" 

# VARS
Connected = False #global variable for the state of the connection


def get_secrets():
    ''' GET configuration data '''
    global MQTT_HOST
    global MQTT_PASSWORD
    global MQTT_USERNAME
    global MQTT_TOPIC
    global MQTT_PUB
    global PORTA
    global INTERVALO
    global ENVIA_JSON
    global ENVIA_MUITOS
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
        MQTT_PUB = config.get('secrets', 'MQTT_PUB')
        PORTA = config.get('config','PORTA')
        INTERVALO = config.get('config','INTERVALO')
        ENVIA_JSON = config.get('config','ENVIA_JSON')
        ENVIA_MUITOS = config.get('config','ENVIA_MUITOS')
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


def send_command(cmd_name, cmd_string):
    print ("\ncmd_name:", cmd_name)
    print ("cmd_string:", cmd_string)
    cmd_bytes = bytearray.fromhex(cmd_string)
    for cmd_byte in cmd_bytes:
        hex_byte = ("{0:02x}".format(cmd_byte))
        #print (hex_byte)
        ser.write(bytearray.fromhex(hex_byte))
        time.sleep(.100)
    response = ser.read(32)
    respHex = binascii.hexlify(bytearray(response))
    print ("response:", respHex)
    return respHex


def chk(st):
    ''' 8-bit checksum 0x100 '''
    soma = 0
    xp = st.split()
    for i in xp:
        soma = soma + int(i.encode('ascii'),16)
    if soma >= 0x100:
        soma = soma % 0x100 # soma = soma - 0x100
    ret = 0x100 - soma
    if ret==256: ret = 0
    ret = hex(ret).upper()
    ret = ret.replace("X","x")
    return ret

def trataRetorno(rawData):
    rData = rawData.lower()
    if type(rData) is str:  # arruma quando é string
        rData = bytearray.fromhex(rData)
        rData = binascii.hexlify(rData)
    tmp = []
    if rData[0:2] != b'3d':
        print ('Erro na string')
        exit()
    tmp.append(rData[0:2])   # 0
    tmp.append(rData[2:6])   # 1
    tmp.append(rData[6:10])  # 2
    tmp.append(rData[10:14]) # 3
    tmp.append(rData[14:18]) # 4
    tmp.append(rData[18:22]) # 5
    tmp.append(rData[22:26]) # 6
    tmp.append(rData[26:30]) # 7
    tmp.append(rData[30:32]) # 8
    tmp.append(rData[32:34]) # 9
    tmp.append(rData[34:36]) #10
    return tmp


def toINT16(valorHex):
    ''' Para Int 16 '''
    ret = int(valorHex,16)
    return ret


def dadosNoBreak(lista):
    ''' Dados para as variaveis certas '''
    noBreak = {'lastinputVac':0,
        'inputVac':0,
        'outputVac':0,
        'outputpower':0,
        'outputHz':0,
        'batterylevel':0,
        'temperatureC':0,
        'BeepLigado': False,
        'ShutdownAtivo': False,
        'TesteAtivo': False,
        'UpsOk': False,
        'Boost': False,
        'ByPass': False,
        'BateriaBaixa': False,
        'BateriaLigada': False
         }
    noBreak['lastinputVac'] = toINT16(lista[1])/10
    noBreak['inputVac'] = toINT16(lista[2])/10
    noBreak['outputVac'] = toINT16(lista[3])/10
    noBreak['outputpower'] = toINT16(lista[4])/10
    noBreak['outputHz'] = toINT16(lista[5])/10
    noBreak['batterylevel'] = toINT16(lista[6])/10
    noBreak['temperatureC'] = toINT16(lista[7])/10
    bi = "{0:08b}".format(toINT16(lista[8]))
    bj = "{0:08b}".format(toINT16(lista[9]))
    noBreak['BeepLigado'] = bi[0]
    noBreak['ShutdownAtivo'] = bi[1]
    noBreak['TesteAtivo'] = bi[2]
    noBreak['UpsOk'] = bi[3]
    noBreak['Boost'] = bi[4]
    noBreak['ByPass'] = bi[5]
    noBreak['BateriaBaixa'] = bi[6]
    noBreak['BateriaLigada'] = bi[7]
    noBreak['*BeepLigado'] = bj[0]
    noBreak['*ShutdownAtivo'] = bj[1]
    noBreak['*TesteAtivo'] = bj[2]
    noBreak['*UpsOk'] = bi[3]
    noBreak['*Boost'] = bi[4]
    noBreak['*ByPass'] = bi[5]
    noBreak['*BateriaBaixa'] = bi[6]
    noBreak['*BateriaLigada'] = bi[7]
    return noBreak


def mostra_dados(dic):
    ''' mostra os dados na tela '''
    for k,v in dic.items():
        print(k,v)

def test(raw):
    lista_dados = trataRetorno(raw)
    ret = dadosNoBreak(lista_dados)
    print (raw)
    mostra_dados(ret)

def montaCmd(c1, c2):
    ''' Monta comando para enviar para o no-break 
    exemplo: montaCmd('47','ff ff ff ff')
    '''
    
    st = c1 + ' ' + c2
    check = chk(st)
    check = check.replace("0x","")
    ret = st + ' ' + check +  ' ' +  CR 
    return ret

def publish_many(topic, dicionario):
    for key,val in dicionario.items():
        topi = topic + "/" + key
        client.publish(topi, str(val))
        


# APP START

print("** SMS UPS v.0.1")
print ("Starting up...")


get_secrets()

print ("MQTT: " + MQTT_HOST)
print ("pass: " + MQTT_PASSWORD)
print ("user: " + MQTT_USERNAME)


# MQQT Start
client = mqtt.Client()
client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883, 60)
client.loop_start()  # start the loop

while not Connected:
    time.sleep(0.1)  # wait for connection



try:
    ser = serial.Serial(PORTA,
        baudrate=2400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout = 1)
    print ("Porta: " + PORTA + " - " + str(ser.isOpen()))
except:
    print ("Não consegui abrir a porta serial")
    if not ser.isOpen(): ser = ""


# Time entre a conexao serial e o tempo para escrever (enviar algo)
time.sleep(1.8) # Entre 1.5s a 2s


# loop start


while True:
    x = send_command("query",cmd[1])
    lista_dados = trataRetorno(x)
    upsData = dadosNoBreak(lista_dados)
    print ('---------')
    print (x)
    mostra_dados(upsData)
    if ENVIA_JSON:
        jsonUPS = json.dumps(upsData)
        client.publish(MQTT_PUB + "/json", jsonUPS)
    if ENVIA_MUITOS:
        publish_many(MQTT_PUB, upsData)
    time.sleep(INTERVALO)

while 1==2:
    #ser.write(commandToSend)
    #send_command("dados", cmd[1])

    time.sleep(1)
    while True:
        try:
            print ("Attempt to Read")
            #readOut = ser.readline().decode('ascii')
            response = ser.read(18) # 32
            print ("response:", binascii.hexlify(bytearray(response)))
            time.sleep(1)
            print ("Reading: ", readOut) 
            break
        except:
            pass
    print ("Restart")
    ser.flush() #flush the buffer
    time.sleep(20)


# client.loop_forever()

time.sleep(2)
ser.close()



''' Resposta do Q

	01 - 0x3d (=)    - Inicio da resposta
	02 - 0x08		- 0XAA	 - 
	03 - 0x34 (4)	- 0X  AA - lastinputVac
	04 - 0x08		- 0XBB   -
	05 - 0x34 (4)	- 0X  BB - inputVac
	06 - 0x04		- 0XCC   -
	07 - 0x38 (8)	- 0X  CC - outputVac
	08 - 0x01		- 0XDD   -
    09 - 0x22 (")	- 0X  DD - outputpower
	10 - 0x02		- 0XEE   -
	11 - 0x58 (X)	- 0X  EE - outputHz
	12 - 0x03		- 0XFF   -
	13 - 0xe8		- 0X  FF - batterylevel
	14 - 0x01		- 0XGG   -
	15 - 0x7c (|)	- 0X  GG - temperatureC
	16 - 0x29 ())	- HH     - State bits (beepon, shutdown, test, upsok, 
	17 - 0x01		- ??	 - ??	boost, onacpower, lowbattery, onbattery)
	18 - 0x0d		- Final da resposta

  exemplos:
  *     *      *     *     *     *     *     *     *
  01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18
  3d 00 00 08 82 04 50 00 00 02 57 03 e8 01 66 09 31 0d


BeepLigado
ShutdownAtivo
TesteAtivo
UpsOk
Boost
ByPass
BateriaBaixa
BateriaLigada
'''
