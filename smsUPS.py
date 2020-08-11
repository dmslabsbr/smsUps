__author__ = 'dmslabs'

import serial
import time
import struct
import binascii
import os
import paho.mqtt.client as mqtt
import configparser
import json
from datetime import datetime
from string import Template

# CONFIG
SECRETS = 'secrets.ini'
MQTT_HOST = "mqtt.eclipse.org" 
MQTT_USERNAME  = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC  = "$SYS/#"
MQTT_PUB = "home/ups"
MQTT_HASS = "homeassistant"
PORTA = '/dev/tty.usbserial-1440' # '/dev/ttyUSB0'
INTERVALO = 5
ENVIA_JSON = True
ENVIA_MUITOS = True
ENVIA_HASS = True
ECHO = True
UPS_NAME='UPS'
UPS_ID = '01'

# CONST
VERSAO = '0.2'
CR = '0D'
MANUFACTURER = 'dmslabs'
VIA_DEVICE = 'smsUPS'
NODE_ID = 'dmslabs'

respostaH = [None] * 18

cmd = {'Q':"51 ff ff ff ff b3 0d",  # pega_dados "Q"
        'I':"49 ff ff ff ff bb 0d", # retorna nome do no-break - :MNG3 1500 Bi1.2o  "I"  
        'D':"44 ff ff ff ff c0 0d", # para teste de bateria - sem retorno "D"
        'F':"46 ff ff ff ff be 0d", # caracteristicas  "F" - ;EBiS115000 2460o
        'G':"47 01 ff ff ff bb 0d", # ? "G"
        'M':"4d ff ff ff ff b7 0d", # Liga/desliga beep   - sem retorno  "M"
        'T':"54 00 10 00 00 9c 0d", # testa bateria por 10 segundos - sem retorno  - "T"    
        'T1':"54 00 64 00 00 48 0d", # t 1 minuto
        'T2':"54 00 c8 00 00 e4 0d", # t 2 minutos  
        'T3':"54 01 2c 00 00 7f 0d", # t 3 minutos  
        'T9':"54 03 84 00 00 25 0d", # t 9 minutos
        'C':"43 ff ff ff ff c1 0d", # Cancela Teste "C"  - Não cancela o "L"
        'L':"4C ff ff ff ff" # teste bateria baixa "L" 
    }

# VARS
Connected = False #global variable for the state of the connection

noBreakInfo = {'name':'',
    'info':''} 

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
    'BateriaLigada': False,
    'time': "",
    'info': "",
    'name': ''}


json_hass = {"sensor": '''
{ 
  "stat_t": "home/ups/json",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "icon": "$icon",
  "device_class": "$device_class",
  "device": { $device_dict }
}''',
    "binary_sensor": '''
{ 
  "stat_t": "home/ups/json",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "device_class": "$device_class",
  "device": { $device_dict },
  "pl_on": "$pl_on",
  "pl_off": "$pl_off",
  "pl_avail": "$pl_avail",
  "pl_not_avail": "$pl_not_avail",
}
'''}

device_dict = ''' "name": "$device_name",
    "manufacturer": "$manufacturer",
    "model": "$model",
    "sw_version": "$sw_version",
    "via_device": "$via_device",
    "identifiers": [ "$identifiers" ] '''

sensor_dic = ""


def get_secrets():
    ''' GET configuration data '''
    global MQTT_HOST
    global MQTT_PASSWORD
    global MQTT_USERNAME
    global MQTT_TOPIC
    global MQTT_PUB
    global MQTT_HASS
    global PORTA
    global INTERVALO
    global ENVIA_JSON
    global ENVIA_MUITOS
    global ENVIA_HASS
    global ECHO
    global UPS_NAME
    global UPS_ID
    try:
        from configparser import ConfigParser
        config = ConfigParser()
    except ImportError:
        from ConfigParser import ConfigParser  # ver. < 3.0
    try:
        config.read(SECRETS)
        MQTT_PASSWORD = config.get('secrets', 'MQTT_PASS')
        MQTT_USERNAME  = config.get('secrets', 'MQTT_USER')
        MQTT_HOST = config.get('secrets', 'MQTT_HOST')
        MQTT_TOPIC = config.get('config', 'MQTT_TOPIC')
        MQTT_PUB = config.get('config', 'MQTT_PUB')
        MQTT_HASS = config.get('config', 'MQTT_HASS')
        PORTA = config.get('config','PORTA')
        INTERVALO = int(config.get('config','INTERVALO'))
        ENVIA_JSON = config.get('config','ENVIA_JSON')
        ENVIA_MUITOS = config.get('config','ENVIA_MUITOS')
        ENVIA_HASS = config.get('config','ENVIA_HASS')
        ECHO = config.get('config','ECHO')
        UPS_NAME = config.get('device','UPS_NAME') 
        UPS_ID = config.get('device','UPS_ID') 

        if ENVIA_HASS: ENVIA_JSON = True
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
    res = json.loads(msg.payload)
    if ECHO: print(msg.topic+" "+str(msg.payload))
    v=res['cmd'].upper()
    if v=='T':
        send_command("Test",cmd['T'])
    elif v=="M":
        send_command("Beep",cmd['M'])
    elif v=="C":
        send_command("Cancel",cmd['C'])
    elif v=="RAW":
        # envia comando como recebido
        ret = send_command("Raw",res['val'])
        if len(ret)>0:
            client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="CMD":
        # envia comando e inclui checksum
        if len(res['val'])!=0:
            comando = montaCmd(res['val'])
            ret = send_command("CMD", comando)
            if len(ret)>0:
                client.publish(MQTT_PUB + "/result", str(ret))
        else:
            client.publish(MQTT_PUB + "/result", "Invalid command")

    time.sleep(.500)
    queryQ()


def send_command(cmd_name, cmd_string):
    if ECHO: print ("\ncmd_name:", cmd_name)
    if ECHO: print ("cmd_string:", cmd_string)
    cmd_bytes = bytearray.fromhex(cmd_string)
    for cmd_byte in cmd_bytes:
        hex_byte = ("{0:02x}".format(cmd_byte))
        #print (hex_byte)
        ser.write(bytearray.fromhex(hex_byte))
        time.sleep(.100)
    response = ser.read(32)
    respHex = binascii.hexlify(bytearray(response))
    if ECHO: print ("response:", respHex)
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
    if len(rData)==0: return None
    if type(rData) is str:  # arruma quando é string
        rData = bytearray.fromhex(rData)
        rData = binascii.hexlify(rData)
    tmp = []
    if rData[0:2] != b'3d':
        print ('Erro na string')
        return None
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
    global noBreak
    if lista is None:
        print ("No UPS Data")
        lista = ["0"] * 15
    noBreak['time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    noBreak['lastinputVac'] = toINT16(lista[1])/10
    noBreak['inputVac'] = toINT16(lista[2])/10
    noBreak['outputVac'] = toINT16(lista[3])/10
    noBreak['outputpower'] = toINT16(lista[4])/10
    noBreak['outputHz'] = toINT16(lista[5])/10
    noBreak['batterylevel'] = toINT16(lista[6])/10
    noBreak['temperatureC'] = toINT16(lista[7])/10
    bi = "{0:08b}".format(toINT16(lista[8]))
    bj = "{0:08b}".format(toINT16(lista[9]))
    noBreak['BeepLigado'] = bi[7]     # Beep Ligado
    noBreak['ShutdownAtivo'] = bi[6]  # ShutdownAtivo
    noBreak['TesteAtivo'] = bi[5]     # teste ativo
    noBreak['UpsOk'] = bi[4]          # upsOK / Vcc na saída
    noBreak['Boost'] = bi[3]          # Boost / Potência de Saída Elevada
    noBreak['ByPass'] = bi[2]         # byPass
    noBreak['BateriaBaixa'] = bi[1]   # Bateria Baixa / Falha de Bateria
    noBreak['BateriaLigada'] = bi[0]  # Bateria Ligada / em uso
    noBreak['RedeEletrica'] = "ver"  # Rede Elétrica / Vcc na entrada

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

def montaCmd(c1):
    ''' Monta comando para enviar para o no-break 
    exemplo: montaCmd('47 ff ff ff ff')
    '''
    
    st = c1
    check = chk(st)
    check = check.replace("0x","")
    ret = st + ' ' + check +  ' ' +  CR 
    return ret

def publish_many(topic, dicionario):
    for key,val in dicionario.items():
        topi = topic + "/" + key
        client.publish(topi, str(val))
        
def hex2Ascii(hexa):
    res = str(hexa).replace("b'","").replace("'","")
    try:
        res = bytes.fromhex(res).decode('utf-8')
    except ValueError:
        res = ""
    return res

def getNoBreakInfo():
    global noBreakInfo
    if len(noBreakInfo['name']) == 0:
        # get nobreak data
        res = send_command("Name",cmd['I'])
        noBreakInfo['name'] = hex2Ascii(res)
        if noBreakInfo['info'] == '':
            # get nobreak data
            res = send_command("Info",cmd['F'])
            noBreakInfo['info'] = hex2Ascii(res)
        if len(noBreakInfo['name'])+len(noBreakInfo['name'])<5:
            noBreakInfo['name'] = UPS_NAME
            noBreakInfo['info'] = 'no info'

def queryQ():
    ''' get ups data and publish'''
    x = send_command("query",cmd['Q'])
    lista_dados = trataRetorno(x)
    upsData = dadosNoBreak(lista_dados)
    if ECHO:
        print ('---------')
        print (x)
        mostra_dados(upsData)
    if ENVIA_JSON:
        jsonUPS = json.dumps(upsData)
        client.publish(MQTT_PUB + "/json", jsonUPS)
    if ENVIA_MUITOS:
        publish_many(MQTT_PUB, upsData)
    return upsData

def json_remove_vazio(strJson):
    ''' remove linhas / elementos vazios de uma string Json '''
    dados = json.loads(strJson)  # converte string para dict
    cp_dados = json.loads(strJson) # cria uma copia
    for k,v in dados.items():
        if len(v) == 0:
            cp_dados.pop(k)  # remove vazio
    return json.dumps(cp_dados) # converte dict para json

def send_hass():
    ''' Envia parametros para incluir device no hass.io '''
    global sensor_dic
    component = "sensor"

    # var comuns
    varComuns = {'sw_version': VERSAO,
                 'model': noBreakInfo['info'],
                 'manufacturer': MANUFACTURER,
                 'device_name': noBreakInfo['name'],
                 'identifiers': noBreakInfo['name'] + "_" + UPS_ID,
                 'via_device': VIA_DEVICE,
                 'uniq_id': UPS_ID}
    if sensor_dic == "":
        json_file = open('sensor.json')
        json_str = json_file.read()
        sensor_dic = json.loads(json_str)
    key_todos = sensor_dic['todos']
    sensor_dic.pop('todos')
    for key,dic in sensor_dic.items():
        print(key,dic)
        varComuns['uniq_id']=varComuns['identifiers']+"_" + key
        dic['val_tpl']=dic['name']
        dic['name']=varComuns['uniq_id']
        dic['device_dict'] = device_dict
        dados = Template(json_hass[component]) # sensor
        dados = Template(dados.safe_substitute(dic))
        dados = Template(dados.safe_substitute(varComuns)) # faz ultimas substituições
        dados = dados.safe_substitute(key_todos) # remove os não substituidos.
        topico = MQTT_HASS + "/" + component + "/" + NODE_ID + "/" + varComuns['uniq_id'] + "/config"
        print(topico)
        print(dados)
        dados = json_remove_vazio(dados)
        client.publish(topico, dados)


# APP START

print("** SMS UPS v." + VERSAO)
print ("Starting up...")


get_secrets()

'''
print ("MQTT: " + MQTT_HOST)
print ("pass: " + MQTT_PASSWORD)
print ("user: " + MQTT_USERNAME)
'''

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


if ENVIA_HASS:
    getNoBreakInfo()
    send_hass()

# loop start
while True:
    queryQ()
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
