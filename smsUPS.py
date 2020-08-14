__author__ = 'dmslabs'

import serial
import time
import struct
import binascii
import os
import paho.mqtt.client as mqtt
import configparser
import json
import logging
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
PORTA = '/dev/tty.usbserial-1470, /dev/tty.usbserial-1440, /dev/ttyUSB0'
INTERVALO = 30
INTERVALO_HASS = 600
INTERVALO_DISCOVERY = 600
ENVIA_JSON = True
ENVIA_MUITOS = True
ENVIA_HASS = True
ECHO = True
UPS_NAME='UPS'
UPS_ID = '01'
SMSUPS_SERVER = True
SMSUPS_CLIENTE = True
LOG_FILE = '/var/tmp/smsUPS.log'
SHUTDOWN_CMD = '"shutdown /s /t 1", "sudo shutdown now", "systemctl poweroff"'

LOG_LEVEL = logging.DEBUG


# CONST
VERSAO = '0.4'
CR = '0D'
MANUFACTURER = 'dmslabs'
VIA_DEVICE = 'smsUPS'
NODE_ID = 'dmslabs'
APP_NAME = 'smsUPS'

respostaH = [None] * 18

cmd = {'Q':"51 ff ff ff ff b3 0d",  # pega_dados "Q"
        'I':"49 ff ff ff ff bb 0d", # retorna nome do no-break - :MNG3 1500 Bi1.2o  "I"  
        'D':"44 ff ff ff ff c0 0d", # para teste de bateria - sem retorno "D"
        'F':"46 ff ff ff ff be 0d", # caracteristicas  "F" - ;EBiS115000 2460o
        'G':"47 01 ff ff ff bb 0d", # ? "G"
        'M':"4d ff ff ff ff b7 0d", # Liga/desliga beep   - sem retorno  "M"
        'T':"54 00 10 00 00 9c 0d", # testa bateria por 10 segundos - sem retorno  - "T"    
        'T1':"54 00 64 00 00 48 0d", # t 100 s
        'T2':"54 00 c8 00 00 e4 0d", # t 200 s  
        'T3':"54 01 2c 00 00 7f 0d", # t 300 s  
        'T9':"54 03 84 00 00 25 0d", # t 900 s
        'C':"43 ff ff ff ff c1 0d", # Cancela Teste "C"  - Não cancela o "L"
        'L':"4C ff ff ff ff" # teste bateria baixa "L" 
    }

# VARS
Connected = False #global variable for the state of the connection
devices_enviados = False  # Global - Controla quando enviar novamente o cabeçalho para autodiscovery
serialOk = False
porta_atual = 0

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

status = {"ip":"?",
          "serial": False,
          "ups": False,
          "mqqt": False}
          

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
  "pl_not_avail": "$pl_not_avail"
}
''',
    "switch": '''
{ 
  "stat_t": "home/ups/json",
  "name": "$name",
  "cmd_t":"$cmd_t",
  "icon":"$icon",
  "uniq_id": "$uniq_id",
  "val_tpl": "$val_tpl",
  "device": { $device_dict },
  "pl_on": "$pl_on",
  "pl_off": "$pl_off",
  "pl_avail": "$pl_avail",
  "pl_not_avail": "$pl_not_avail",
  "qos": "0"
}
'''}

device_dict = ''' "name": "$device_name",
    "manufacturer": "$manufacturer",
    "model": "$model",
    "sw_version": "$sw_version",
    "via_device": "$via_device",
    "identifiers": [ "$identifiers" ] '''

sensor_dic = dict() # {}

def get_config (config, topic, key, default, getBool = False, getInt = False):
    ''' Read config data '''
    ret = default
    try:
        ret = config.get(topic, key)
        if getBool or type(default) is bool: ret = config.getboolean(topic, key)
        if getInt or type(default) is int: ret = config.getint(topic, key)
    except:
        ret = default
    return ret

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
    global INTERVALO_HASS
    global ENVIA_JSON
    global ENVIA_MUITOS
    global ENVIA_HASS
    global ECHO
    global UPS_NAME
    global UPS_ID
    global SMSUPS_SERVER
    global SMSUPS_CLIENTE
    global LOG_FILE
    global SHUTDOWN_CMD
    print ("Getting config file.")
    #log.debug("Getting config file.")
    try:
        from configparser import ConfigParser
        config = ConfigParser()
    except ImportError:
        from ConfigParser import ConfigParser  # ver. < 3.0
    try:
        config.read(SECRETS)
    except:
        log.warning("Can't load config. Using default config.")
        print ("defalt config")
    # le os dados
    MQTT_PASSWORD = get_config(config, 'secrets', 'MQTT_PASS', MQTT_PASSWORD)
    MQTT_USERNAME  = get_config(config, 'secrets', 'MQTT_USER', MQTT_USERNAME)
    MQTT_HOST = get_config(config, 'secrets', 'MQTT_HOST', MQTT_HOST)
    MQTT_TOPIC = get_config(config, 'config', 'MQTT_TOPIC', MQTT_TOPIC)
    MQTT_PUB = get_config(config, 'config', 'MQTT_PUB', MQTT_PUB)
    MQTT_HASS = get_config(config, 'config', 'MQTT_HASS', MQTT_HASS)
    PORTA = get_config(config, 'config','PORTA', PORTA)
    PORTA = PORTA.split(',') # caso mais de uma porta
    INTERVALO = get_config(config, 'config','INTERVALO', INTERVALO, getInt=True)
    INTERVALO_HASS = get_config(config, 'config','INTERVALO_HASS', INTERVALO_HASS, getInt=True)
    ENVIA_JSON = get_config(config, 'config','ENVIA_JSON', ENVIA_JSON, getBool=True)
    ENVIA_MUITOS = get_config(config, 'config','ENVIA_MUITOS', ENVIA_MUITOS, getBool=True)
    ENVIA_HASS = get_config(config, 'config','ENVIA_HASS', ENVIA_HASS, getBool=True)
    ECHO = get_config(config, 'config','ECHO', ECHO, getBool=True)
    UPS_NAME = get_config(config, 'device','UPS_NAME', UPS_NAME) 
    UPS_ID = get_config(config, 'device','UPS_ID', UPS_ID) 
    SMSUPS_SERVER = get_config(config, 'config', 'SMSUPS_SERVER', SMSUPS_SERVER, getBool=True)
    SMSUPS_CLIENTE = get_config(config, 'config', 'SMSUPS_CLIENTE', SMSUPS_CLIENTE, getBool=True)
    LOG_FILE = get_config(config, 'config', 'LOG_FILE', LOG_FILE)
    SHUTDOWN_CMD = get_config(config, 'config', 'SHUTDOWN_CMD', SHUTDOWN_CMD)
    SHUTDOWN_CMD = SHUTDOWN_CMD.split(',')

    for i in range(len(SHUTDOWN_CMD)):
        SHUTDOWN_CMD[i] = SHUTDOWN_CMD[i].replace('"','').replace("'", '')
    if ENVIA_HASS: ENVIA_JSON = True

def shutdown_computer():
    ''' try to shutdown the computer '''
    log.warning('tring to shutdown the computer')
    import sys
    p = 'sys.platform: ' + sys.platform
    print (p)
    log.info(p)
    if sys.platform == 'win32':
        import ctypes
        user32 = ctypes.WinDLL('user32')
        user32.ExitWindowsEx(0x00000008, 0x00000000)
    else:
        import os
        for i in range(len(SHUTDOWN_CMD)):
            command = SHUTDOWN_CMD[i]  # trying many commands
            os.system(command) # 'sudo shutdown now'

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global Connected
    global status
    print("Connected with result code "+str(rc))
    log.debug("Connected with result code "+str(rc))
    if rc == 0:
        print ("Connected to " + MQTT_HOST)
        Connected = True
        client.connected_flag=True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(MQTT_TOPIC)
    else:
        tp_c = {0: "Connection successful",
                1: "Connection refused – incorrect protocol version",
                2: "Connection refused – invalid client identifier",
                3: "Connection refused – server unavailable",
                4: "Connection refused – bad username or password",
                5: "Connection refused – not authorised",
                100: "Connection refused - other things"
        }
        Connected = False
        if rc>5: rc=100
        print (rc + tp_c[rc])
        log.error(rc + tp_c[rc])
        # tratar quando for 3 e outros
    if Connected:
        status['mqqt'] = "on"
    else:
        status['mqqt'] = "off"

def on_disconnect(client, userdata, rc):
    global Connected
    global devices_enviados
    Connected = False
    log.info("disconnecting reason  "  +str(rc))
    print("disconnecting reason  "  +str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
    devices_enviados = False # Force sending again
    status['mqqt'] = "off"

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        res = json.loads(msg.payload)
    except Exception as e:
        if e.__class__.__name__ == 'JSONDecodeError':
            msg_p = msg.payload
            msg_p = msg_p.decode()
            msg_p = msg_p.replace("'",'"')
            res = json.loads(msg_p)
        else:
            err_msg = 'Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e))
            print(err_msg)
            log.warning (err_msg)
    if ECHO: 
        print(msg.topic+" "+str(msg.payload))
        print(res)
    log.debug("on_message:" + msg.topic + str(msg.payload))
    v=res['cmd'].upper()
    if v=='T':
        ret = send_command("Test",cmd['T'])
        client.publish(MQTT_PUB + "/result", str(ret))
    if v=='TN':
        if len(res['val'])!=0:
            val = res['val']
            if type(val) is int:
                comando = tempo2hexCMD(val)
        ret = send_command("Test",cmd['T'])  # teste N minutes
        client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="M":
        ret = send_command("Beep",cmd['M'])
        client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="C":
        ret = send_command("Cancel",cmd['C'])
        client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="L":
        ret = send_command("TestLow",cmd['L'])
        client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="RAW":
        # envia comando como recebido
        ret = send_command("Raw",res['val'])
        if len(ret)>0:
            log.debug("publish: " + MQTT_PUB + "/result : " + str(ret))
            client.publish(MQTT_PUB + "/result", str(ret))
    elif v=="CMD":
        # envia comando e inclui checksum
        if len(res['val'])!=0:
            comando = montaCmd(res['val'])
            ret = send_command("CMD", comando)
            if len(ret)>0:
                log.debug("publish: " + MQTT_PUB + "/result : " + str(ret))
                client.publish(MQTT_PUB + "/result", str(ret))
        else:
            log.debug("publish: " + MQTT_PUB + "/result : Invalid command")
            client.publish(MQTT_PUB + "/result", "Invalid command")

    time.sleep(.500)
    queryQ()


def send_command(cmd_name, cmd_string):
    ''' envia um comando para o nobreak '''
    global serialOk
    respHex = ""
    log.debug("send-cmd - serialok:" + str(serialOk))
    if serialOk:
        if ECHO: print ("\ncmd_name:", cmd_name)
        if ECHO: print ("cmd_string:", cmd_string)
        log.debug ("cmd:" + cmd_name + " / str: " + cmd_string)
        cmd_bytes = bytearray.fromhex(cmd_string)
        for cmd_byte in cmd_bytes:
            hex_byte = ("{0:02x}".format(cmd_byte))
            #print (hex_byte)
            ser.write(bytearray.fromhex(hex_byte))
            time.sleep(.100)
        response = ser.read(32)
        respHex = binascii.hexlify(bytearray(response))
        if ECHO: print ("response:", respHex)
        log.debug ("response: " + str(respHex))
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
        log.debug('String error!')
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
        log.debug ("No UPS Data")
        lista = ["1"] * 15
        lista[1] = "0"
        lista[2] = "0"
        lista[3] = "0"
        lista[4] = "0"
        lista[5] = "0"
        lista[6] = "0"
        lista[7] = "0"
        lista[8] = "FF"
        lista[9] = "FF"
    noBreak['time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    noBreak['lastinputVac'] = toINT16(lista[1])/10
    noBreak['inputVac'] = toINT16(lista[2])/10
    noBreak['outputVac'] = toINT16(lista[3])/10
    noBreak['outputpower'] = toINT16(lista[4])/10
    noBreak['outputHz'] = toINT16(lista[5])/10
    noBreak['batterylevel'] = toINT16(lista[6])/10
    noBreak['temperatureC'] = toINT16(lista[7])/10
    bi = "{0:08b}".format(toINT16(lista[8]))
    # bj = "{0:08b}".format(toINT16(lista[9]))
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


def tempo2hexCMD(i):
    '''  Converte um int para hex para ser enviado ''''
    if not type(i) is int:
        log.error ('i must be an integer.') 
        i = 0
    if i > 3600:
        log.warning ('tempo2hex: Valor de i > 3600. i=' + i)
        i = 3600
    ret = "000000" + hex(i)[2:]
    ret = ret[-4:].upper()
    ret = ret[0:2] + " " + ret[2:5]
    ret = cmd['T'][0:2] + " " + ret + "00 00"
    ret = montaCmd(ret)
    return ret


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
    global status
    if len(noBreakInfo['name']) == 0:
        # get nobreak data
        res = send_command("Name",cmd['I'])
        noBreakInfo['name'] = hex2Ascii(res)
        if noBreakInfo['info'] == '':
            # get nobreak data
            res = send_command("Info",cmd['F'])
            noBreakInfo['info'] = hex2Ascii(res)
        if noBreakInfo['name'] == '' or not noBreakInfo['name'][0] == ":": # len(noBreakInfo['name'])+len(noBreakInfo['name'])<5:
            noBreakInfo['name'] = UPS_NAME
            noBreakInfo['info'] = 'no info'
            status['ups'] = 'off'
        else:
            noBreakInfo['name'] = noBreakInfo['name'][1:]
            status['ups'] = 'Connected'
    if noBreakInfo['name'][-1:] == '\r': noBreakInfo['name'] = noBreakInfo['name'][0:-1]
    if noBreakInfo['info'][-1:] == '\r': noBreakInfo['info'] = noBreakInfo['info'][0:-1]
    if noBreakInfo['info'][0] == ';': noBreakInfo['info'] = noBreakInfo['info'][1:]
    log.debug ("UPS Info: " + 
        noBreakInfo['name'] + " / " + 
        noBreakInfo['info'])

def queryQ():
    ''' get ups data and publish'''
    global status
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
    if ENVIA_JSON or ENVIA_HASS or ENVIA_MUITOS:
        if status['serial'] == 'open' and  \
           status['ups'] == 'Connected' and \
           status['mqqt'] == 'on': 
            status[APP_NAME] = "on"
        else:
            status[APP_NAME] = "off"
        jsonStatus = json.dumps(status)
        client.publish(MQTT_PUB + "/status", jsonStatus)
    return upsData

def json_remove_vazio(strJson):
    ''' remove linhas / elementos vazios de uma string Json '''
    strJson.replace("\n","")
    dados = json.loads(strJson)  # converte string para dict
    cp_dados = json.loads(strJson) # cria uma copia
    for k,v in dados.items():
        if len(v) == 0:
            cp_dados.pop(k)  # remove vazio
    return json.dumps(cp_dados) # converte dict para json

def monta_publica_topico(component, sDict, varComuns):
    ''' monta e envia topico '''
    key_todos = sDict['todos']
    sDict.pop('todos')
    for key,dic in sDict.items():
        print(key,dic)
        varComuns['uniq_id']=varComuns['identifiers']+"_" + key
        if not('val_tpl' in dic):
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
        log.debug ("topico: " + topico)
        client.publish(topico, dados)


def send_hass():
    ''' Envia parametros para incluir device no hass.io '''
    global sensor_dic
    global devices_enviados

    # var comuns
    varComuns = {'sw_version': VERSAO,
                 'model': noBreakInfo['info'],
                 'manufacturer': MANUFACTURER,
                 'device_name': noBreakInfo['name'],
                 'identifiers': UPS_NAME + "_" + UPS_ID,
                 'via_device': VIA_DEVICE,
                 'uniq_id': UPS_ID}
    
    if len(sensor_dic) == 0:
        for k in json_hass.items():
            json_file = open(k[0] + '.json')
            json_str = json_file.read()
            sensor_dic[k[0]] = json.loads(json_str)

    for k in sensor_dic.items():
        print('Componente:' + k[0])
        monta_publica_topico(k[0], sensor_dic[k[0]], varComuns)

    devices_enviados = True

def abre_serial():
    ''' abre a porta serial '''
    global ser
    global serialOk
    global status
    global porta_atual
    porta_ser = PORTA[porta_atual].strip()

    try:
        ser = serial.Serial(porta_ser,
            baudrate=2400,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = 1)
        print ("Porta: " + porta_ser + " - " + str(ser.isOpen()))
        log.debug ("Port " + porta_ser + " - is open: " + str(ser.isOpen()))
        serialOk = ser.isOpen() # True
        status['serial'] = "open"
    except:
        print ("I was unable to open the serial port ", porta_ser)
        log.warning ("I was unable to open the serial port " + porta_ser)
        status['serial'] = 'off'
        serialOk = False
        # verifica outras portas se for servidor
        if SMSUPS_SERVER:
            porta_atual+=1   # add 1
            if porta_atual > len(PORTA)-1:
                porta_atual = 0
        '''       Não precisa mais - fica tentando.
        if SMSUPS_SERVER and not SMSUPS_CLIENTE:
            print ("I'm going to stop the program.")
            log.critical ("I'm going to stop the program.")
            raise SystemExit(0)
        '''
    return serialOk



# APP START

print("** SMS UPS v." + VERSAO)
print ("Starting up...")

#LOG
log = logging.getLogger('smsUPS')
hdlr = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr) 
log.setLevel(LOG_LEVEL)

log.debug("** SMS UPS v." + VERSAO)
log.debug("Starting up...")

get_secrets()

# MQTT Start
log.info("Starting MQTT " + MQTT_HOST)
client = mqtt.Client()
client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(MQTT_HOST, 1883, 60)
client.loop_start()  # start the loop
log.info("MQTT OK")


while not Connected:
    time.sleep(1)  # wait for connection

serialOk = False

if not serialOk:
    if SMSUPS_SERVER: serialOk = abre_serial()


# Time entre a conexao serial e o tempo para escrever (enviar algo)
time.sleep(1.8) # Entre 1.5s a 2s


if SMSUPS_SERVER:
    getNoBreakInfo()
    if ENVIA_HASS:
        send_hass()

# loop start
while True:
    if SMSUPS_SERVER:  # só se for servidor
        queryQ()  # Get UPS data
        if ENVIA_HASS:
            if devices_enviados and Connected and SMSUPS_SERVER:
                send_hass
        if not serialOk:
            serialOk = abre_serial()
    time.sleep(INTERVALO) # dá um tempo


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
