# -*- coding: utf-8 -*-
__author__ = 'dmslabs'

from ast import Pass
import serial
import time
import struct
import binascii
import os
import pathlib
import paho.mqtt.client as mqtt
import configparser
import json
import logging
import uuid
import socket
import signal
import sys
from datetime import datetime, timedelta
from string import Template
from paho.mqtt import client
import dmslibs as dl
from dmslibs import Color, IN_HASSIO, mostraErro, log, pega_url, pega_url2, printC

from flask import Flask
from flask import render_template
import comum
import webserver
import multiprocessing
from multiprocessing import Process, Pipe

#TODO: Padronizar o formato do tempo impresso  datetime.now() e outros.

# CONFIG
SECRETS = 'secrets.ini'
# CONFIG Secrets
MQTT_HOST = "mqtt.eclipse.org" 
MQTT_USERNAME  = ""
MQTT_PASSWORD  = ""
# CONFIG CONFIG
PORTA = '/dev/tty.usbserial-1470, /dev/tty.usbserial-1440, /dev/ttyUSB0'
SERIAL_PORT_TIMEOUT = 10
INTERVALO_MQTT = 120   #   How often to send data to the MQTT server?
INTERVALO_HASS = 600   # How often to send device information in a format compatible with Home Asssistant MQTT discovery?
INTERVALO_SERIAL = 3 # How often do I read UPS information on the serial port?
SERIAL_CHECK_ALWAYS = 'temperatureC, batterylevel, UpsOk, BateriaBaixa, BateriaEmUso'
MQTT_TOPIC  = "$SYS/#"
MQTT_PUB = "home/ups"
MQTT_HASS = "homeassistant"
ENVIA_JSON = True
ENVIA_MUITOS = True
ENVIA_HASS = True
ECHO = True
SMSUPS_SERVER = True
SMSUPS_CLIENTE = True
LOG_FILE = '/var/tmp/smsUPS.log'
LOG_LEVEL = logging.DEBUG
ALLOW_SHUTDOWN = True
DEVELOPERS_MODE = False
SHUTDOWN_CMD = '"sudo shutdown -h now", "sudo shutdown now", "systemctl poweroff", "sudo poweroff"'
# CONFIG Device
UPS_NAME='UPS'
UPS_ID = '01'
UPS_NAME_ID = 'UPS_01'
SMSUPS_FULL_POWER = 1450
UPS_BATERY_LEVEL = 30
UPS_INPUT_VAC = 50
# HASS
Long_lived_access_token = ""
MY_DEVELOPERS_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIyYTk3MmIyZjY3Yzk0OTYyOWI4MzJhY2VlMDQ2MTI1ZSIsImlhdCI6MTYxNDk3NzQ3NCwiZXhwIjoxOTMwMzM3NDc0fQ.26_bRAvcPMc4SFCEZwviHGrSTBtOq6fYbPMyHmn2QY8"
HASS_CMD_NOTIFY = '''echo `curl -sS -X POST \
    -H "Authorization: Bearer $Long_lived_access_token" \
    -H "Content-Type: application/json" \
    -d '{"message": "$message", "title": "$titulo" $outro}' \
    http://homeassistant:8123/api/services/persistent_notification/create `
'''
HASS_DEFAULT_SHUTDOWN_ID = "54543122"
HASS_DEFAULT_NOENERGY_ID = "54543123"
WEB_SERVER = True

class Color:
    # Foreground
    F_Default = "\x1b[39m"
    F_Black = "\x1b[30m"
    F_Red = "\x1b[31m"
    F_Green = "\x1b[32m"
    F_Yellow = "\x1b[33m"
    F_Blue = "\x1b[34m"
    F_Magenta = "\x1b[35m"
    F_Cyan = "\x1b[36m"
    F_LightGray = "\x1b[37m"
    F_DarkGray = "\x1b[90m"
    F_LightRed = "\x1b[91m"
    F_LightGreen = "\x1b[92m"
    F_LightYellow = "\x1b[93m"
    F_LightBlue = "\x1b[94m"
    F_LightMagenta = "\x1b[95m"
    F_LightCyan = "\x1b[96m"
    F_White = "\x1b[97m"
    # Background
    B_Default = "\x1b[49m"
    B_Black = "\x1b[40m"
    B_Red = "\x1b[41m"
    B_Green = "\x1b[42m"
    B_Yellow = "\x1b[43m"
    B_Blue = "\x1b[44m"
    B_Magenta = "\x1b[45m"
    B_Cyan = "\x1b[46m"
    B_LightGray = "\x1b[47m"
    B_DarkGray = "\x1b[100m"
    B_LightRed = "\x1b[101m"
    B_LightGreen = "\x1b[102m"
    B_LightYellow = "\x1b[103m"
    B_LightBlue = "\x1b[104m"
    B_LightMagenta = "\x1b[105m"
    B_LightCyan = "\x1b[106m"
    B_White = "\x1b[107m"

# CONST
VERSAO = '0.41'
CR = '0D'
MANUFACTURER = 'dmslabs'
VIA_DEVICE = 'smsUPS'
NODE_ID = 'dmslabs'
APP_NAME = 'smsUPS'
MQTT_CMD_SHUTDOWN = '{"cmd": "SHUTDOWN","val": "$publish_time"}'
UUID = str(uuid.uuid1())
INTERVALO_EXPIRE = int(INTERVALO_MQTT * INTERVALO_SERIAL)
DEFAULT_MQTT_PASS = "mqtt_pass"
USE_SECRETS = True
SHUTDOWN_CMD_HASS = 'echo `curl -s -X POST -H "Authorization: Bearer $SUPERVISOR_TOKEN" "http://hassio/host/shutdown"`'
SHUTDOWN_CMD_DARWIN = '''osascript -e 'tell app "System Events" to shut down'''

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
        'C':"43 ff ff ff ff c1 0d", # Cancelamento de Shutdown ou restore
        'L':"4C ff ff ff ff", # teste bateria baixa "L" 
        'R': "52 00 C8 27 0F B0 0D", # Shutdown e restore
        "zzz": "52 00 C8 0F EF E0 OD",  # 18/08/2020 19:58  - 15/08 - 23:59:58
        "zz1": "52 01 2C 27 0F 4b OD",  # 16/08 - 00:16:30 - só shutdown
        'S': "53 " # Shutdown em n segundos
    }

# GLOBAL VARS
version_expected = {"dmslibs":2}
Connected = False #global variable for the state of the connection
gDevices_enviados = { 'b': False, 't':datetime.now() }  # Global - Controla quando enviar novamente o cabeçalho para autodiscovery
gMqttEnviado = { 'b': False, 't':datetime.now() }  # Global - Controla quando publicar novamente
serialOk = False
porta_atual = 0
clientOk = False
PATH_ROOT = pathlib.Path().absolute()
PATH_ROOT = str(PATH_ROOT.resolve())
gLastMidMqtt = 0
gBattery = {'time': 0, 'batterylevel': 0}


noBreakInfo = {'name':'',
    'info':''} 

noBreak = {'lastinputVac':0,
    'inputVac':0,
    'outputVac':0,
    'outputPower':0,
    'powerNow':0,
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
    'BateriaEmUso': False,
    'publish_time': "",
    'info': "",
    'name': '',
    'noData': True}

gNoBreakLast = noBreak.copy()

status = {"ip":"?",
          "serial": False,
          "ups": False,
          "mqtt": False}

statusLast = status.copy()
          

json_hass = {"sensor": '''
{ 
  "stat_t": "home/$ups_id/json",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "icon": "$icon",
  "device_class": "$device_class",
  "expire_after": "$expire_after",
  "device": { $device_dict }
}''',
    "binary_sensor": '''
{ 
  "stat_t": "home/$ups_id/json",
  "name": "$name",
  "uniq_id": "$uniq_id",
  "val_tpl": "{{ value_json.$val_tpl }}",
  "device_class": "$device_class",
  "device": { $device_dict },
  "expire_after": "$expire_after",
  "pl_on": "$pl_on",
  "pl_off": "$pl_off",
  "pl_avail": "$pl_avail",
  "pl_not_avail": "$pl_not_avail"
}
''',
    "switch": '''
{ 
  "stat_t": "home/$ups_id/json",
  "name": "$name",
  "cmd_t":"home/$ups_id/cmd",
  "icon":"$icon",
  "uniq_id": "$uniq_id",
  "val_tpl": "$val_tpl",
  "device": { $device_dict },
  "pl_on": "$pl_on",
  "pl_off": "$pl_off",
  "pl_avail": "$pl_avail",
  "pl_not_avail": "$pl_not_avail",
  "qos": "0",
  "state_off": "$state_off",
  "state_on": "$state_on" 
}
'''}

device_dict = ''' "name": "$device_name",
    "manufacturer": "$manufacturer",
    "model": "$model",
    "sw_version": "$sw_version",
    "via_device": "$via_device",
    "identifiers": [ "$identifiers" ] '''

sensor_dic = dict() # {}

def get_config (config, topic, key, default, getBool = False, getInt = False, split = False):
    ''' Read config data '''
    ret = default
    try:
        ret = config.get(topic, key)
        if getBool or type(default) is bool: ret = config.getboolean(topic, key)
        if getInt or type(default) is int: ret = config.getint(topic, key)
    except:
        ret = default
        log.debug('Config: ' + key + " use default: " + str(default))
    if split:
        ret = ret.split(',')
        for i in range(len(ret)):
            ret[i] = ret[i].replace('"','').replace("'", '')
            ret[i] = ret[i].strip()
    return ret

def str2List(texto):
    "Transforma um texto em uma lista"
    ret = texto.split(',')
    for i in range(len(ret)):
        ret[i] = ret[i].replace('"','').replace("'", '')
        ret[i] = ret[i].strip()
    return ret
    
def notifica_n_hass_shutdown(numeroVezes, tempoPorVez):
    if not IN_HASSIO: return None
    for i in range(numeroVezes):
        tempo_restante = int( (numeroVezes-i+1) * tempoPorVez )
        notifica_hass('Going to shutdown in ' + str(tempo_restante),'The computer will shutdown.', HASS_DEFAULT_SHUTDOWN_ID)
        time.sleep(tempoPorVez)

def runNvezes(numeroVezes, tempoPorVez, metodo, keyword_arguments):
    ''' testar melhor '''
    # TODO testar melhor
    for i in range(numeroVezes):
        metodo(*keyword_arguments)
        time.sleep(tempoPorVez)
    return None

def mostraErro(e, nivel=10, msg_add=""):
    err_msg = msg_add + ' / Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e))
    print(Color.F_Red + err_msg + Color.F_Default)
    if nivel == logging.DEBUG: log.debug(err_msg)      # 10
    if nivel == logging.INFO: log.info(err_msg)       # 20
    if nivel == logging.WARNING: log.warning(err_msg)    # 30
    if nivel == logging.ERROR: log.error(err_msg)      # 40
    if nivel == logging.CRITICAL: log.critical(err_msg)   # 50
    # log.warning (err_msg) 

def substitui_secrets():
    "No HASS.IO ADD-ON substitui os dados do secrets.ini pelos do options.json"
    global MQTT_HOST
    global MQTT_PASSWORD
    global MQTT_USERNAME
    global PORTA
    global UPS_NAME
    global UPS_ID
    global UPS_NAME_ID
    global SMSUPS_FULL_POWER
    global MQTT_PUB
    global SMSUPS_SERVER
    global SMSUPS_CLIENTE
    global ALLOW_SHUTDOWN
    global SHUTDOWN_CMD
    global USE_SECRETS
    global Long_lived_access_token
    global DEVELOPERS_MODE
    global FILE_COMM
    global WEB_SERVER

    log.debug ("Loading env data....")
    MQTT_HOST = pegaEnv("MQTT_HOST")
    MQTT_PASSWORD_tmp = pegaEnv("MQTT_PASS")

    DEVELOPERS_MODE = dl.pegaEnv("DEVELOPERS_MODE")
    printC(Color.B_Red, str(DEVELOPERS_MODE))

    
    #DEVELOPERS_MODE = dl.onOff(DEVELOPERS_MODE, True, False)
    #printC(Color.B_Red, str(DEVELOPERS_MODE))


    #if not DEVELOPERS_MODE:
    MQTT_PASSWORD = MQTT_PASSWORD_tmp
    MQTT_USERNAME = pegaEnv("MQTT_USER")
    PORTA = str2List(pegaEnv("PORTA"))
    UPS_NAME = pegaEnv("UPS_NAME")
    UPS_ID = pegaEnv("UPS_ID")
    SMSUPS_FULL_POWER = pegaEnv("SMSUPS_FULL_POWER")
    #UPS_NAME_ID = pegaEnv("UPS_NAME_ID")
    setaUpsNameId()
    SMSUPS_SERVER = str2bool(pegaEnv("SMSUPS_SERVER"))
    SMSUPS_CLIENTE = str2bool(pegaEnv("SMSUPS_CLIENTE"))
    ALLOW_SHUTDOWN = str2bool(pegaEnv("allow_shutdown"))
    SHUTDOWN_CMD = pegaEnv("SHUTDOWN_CMD")
    SHUTDOWN_CMD = str2List(SHUTDOWN_CMD)
    USE_SECRETS = str2bool(pegaEnv("USE_SECRETS"))
    Long_lived_access_token = pegaEnv("Long_lived_access_token")
    if Long_lived_access_token == '' and DEVELOPERS_MODE and IN_HASSIO:
        Long_lived_access_token = MY_DEVELOPERS_ACCESS_TOKEN

    if dl.IN_HASSIO():
        WEB_SERVER = True
        FILE_COMM = '/data/' + comum.FILE_COMM

    log.debug ("Env data loaded.")

def get_secrets():
    ''' GET configuration data '''
    global MQTT_HOST
    global MQTT_PASSWORD
    global MQTT_USERNAME
    global MQTT_TOPIC
    global MQTT_PUB
    global MQTT_HASS
    global PORTA
    global INTERVALO_MQTT
    global INTERVALO_HASS
    global INTERVALO_SERIAL
    global SERIAL_CHECK_ALWAYS
    global ENVIA_JSON
    global ENVIA_MUITOS
    global ENVIA_HASS
    global ECHO
    global UPS_NAME
    global UPS_ID
    global SMSUPS_FULL_POWER
    global UPS_NAME_ID
    global UPS_BATERY_LEVEL
    global SMSUPS_SERVER
    global SMSUPS_CLIENTE
    global LOG_FILE
    global LOG_LEVEL
    global ALLOW_SHUTDOWN
    global DEVELOPERS_MODE
    global SHUTDOWN_CMD
    global SECRETS

    config = getConfigParser()

    print ("Reading secrets.ini")
    log.warning('Reading secrets.ini')

    # le os dados
    MQTT_PASSWORD = get_config(config, 'secrets', 'MQTT_PASS', MQTT_PASSWORD)
    MQTT_USERNAME  = get_config(config, 'secrets', 'MQTT_USER', MQTT_USERNAME)
    MQTT_HOST = get_config(config, 'secrets', 'MQTT_HOST', MQTT_HOST)
    MQTT_TOPIC = get_config(config, 'config', 'MQTT_TOPIC', MQTT_TOPIC)
    MQTT_PUB = get_config(config, 'config', 'MQTT_PUB', MQTT_PUB)
    MQTT_HASS = get_config(config, 'config', 'MQTT_HASS', MQTT_HASS)
    PORTA = get_config(config, 'config','PORTA', PORTA, split = True) # caso mais de uma porta
    INTERVALO_MQTT = get_config(config, 'config','INTERVALO_MQTT', INTERVALO_MQTT, getInt=True)
    INTERVALO_SERIAL = get_config(config, 'config','INTERVALO_SERIAL', INTERVALO_SERIAL, getInt=True)
    INTERVALO_HASS = get_config(config, 'config','INTERVALO_HASS', INTERVALO_HASS, getInt=True)
    SERIAL_CHECK_ALWAYS =  get_config(config, 'config','SERIAL_CHECK_ALWAYS', SERIAL_CHECK_ALWAYS, split = True)
    ENVIA_JSON = get_config(config, 'config','ENVIA_JSON', ENVIA_JSON, getBool=True)
    ENVIA_MUITOS = get_config(config, 'config','ENVIA_MUITOS', ENVIA_MUITOS, getBool=True)
    ENVIA_HASS = get_config(config, 'config','ENVIA_HASS', ENVIA_HASS, getBool=True)
    ECHO = get_config(config, 'config','ECHO', ECHO, getBool=True)
    UPS_NAME = get_config(config, 'device','UPS_NAME', UPS_NAME)
    SMSUPS_FULL_POWER=get_config(config, 'device','SMSUPS_FULL_POWER', SMSUPS_FULL_POWER, getInt=True)
    UPS_ID = get_config(config, 'device','UPS_ID', UPS_ID)
    setaUpsNameId()
    #UPS_NAME_ID = UPS_NAME + "_" + UPS_ID
    #MQTT_PUB = MQTT_PUB + "_" + UPS_NAME_ID
    #UPS_NAME_ID = "ups_" + UPS_NAME_ID
    UPS_BATERY_LEVEL = get_config(config, 'device','UPS_BATERY_LEVEL', UPS_BATERY_LEVEL, getInt=True) 
    SMSUPS_SERVER = get_config(config, 'config', 'SMSUPS_SERVER', SMSUPS_SERVER, getBool=True)
    SMSUPS_CLIENTE = get_config(config, 'config', 'SMSUPS_CLIENTE', SMSUPS_CLIENTE, getBool=True)
    LOG_FILE = get_config(config, 'config', 'LOG_FILE', LOG_FILE)
    LOG_LEVEL = get_config(config, 'config', 'LOG_LEVEL', LOG_LEVEL, getInt=True)
    ALLOW_SHUTDOWN = get_config(config, 'config', 'ALLOW_SHUTDOWN', SMSUPS_CLIENTE, getBool=True)
    DEVELOPERS_MODE = get_config(config = config, topic = 'config',
        key = 'DEVELOPERS_MODE',
        default = DEVELOPERS_MODE,
        getBool=True)
    printC(Color.B_Red, str(DEVELOPERS_MODE))

    SHUTDOWN_CMD = get_config(config, 'config', 'SHUTDOWN_CMD', SHUTDOWN_CMD, split = True)

    if ENVIA_HASS: ENVIA_JSON = True

def str2bool(v):
    '''Para evitar problemas com variaveis booleanas inportadas'''
    ret = v
    if type(v) is bool:
        ret = v
    elif type(v) is str:
        ret = v.lower() in ("yes", "true", "t", "1", "on", "v", "ligado")
    return ret

def getConfigParser():
    print ("Getting Config Parser.")
    bl_existe_secrets = os.path.isfile(SECRETS)
    if bl_existe_secrets:
        log.debug("Existe " + SECRETS)
        print ("Existe " +  SECRETS)
    else:
        log.warning("Não existe " + SECRETS)
        print (Color.F_Magenta, "Não existe " +  SECRETS, Color.F_Default)
        # SECRETS = "/" + SECRETS # tenta arrumar para o HASS.IO
        # O ideal é o SECRETS ficar no data, para não perder a cada iniciada.

    try:
        from configparser import ConfigParser
        config = ConfigParser()
    except ImportError:
        from ConfigParser import ConfigParser  # ver. < 3.0
    try:
        config.read(SECRETS)
    except Exception as e:
        log.warning("Can't load config. Using default config.")
        print ("Can't load config. Using default config.")
        mostraErro(e,20, "get_secrets")
        # ver - INFO get_secrets / Error! Code: DuplicateOptionError, Message,
        #  While reading from 'secrets.ini' [line 22]: option 'log_file' in section 'config' 
        # already exists
    return config

def setaUpsNameId():
    "Seta o UPS_NAME_ID e o MQTT_PUB"
    global UPS_NAME
    global UPS_ID
    global UPS_NAME_ID
    global MQTT_PUB

    name_id = UPS_NAME + "_" + UPS_ID
    UPS_NAME_ID = "ups_" + name_id
    config = getConfigParser()
    MQTT_PUB = get_config(config, 'config', 'MQTT_PUB', MQTT_PUB)
    MQTT_PUB = MQTT_PUB + "_" + name_id


def sigterm_handler(_signo, _stack_frame):
    ''' on_stop / onstop'''
    global status
    # Raises SystemExit(0):
    print ("on_stop")
    log.debug('on_stop')
    status['serial'] = 'off'
    status['ups'] = '?'
    status['mqtt'] = 'off'
    status['smsUPS'] = '?'
    send_clients_status()
    sys.exit(0)

def receive_signal(signum, stack):
    print ('Received: ', signum)
    log.debug('sinal' + str(signum))

def shutdown_computer(s = 120):
    global status
    ''' try to shutdown the computer '''
    log.warning('Trying to shutdown the computer...')
    print (Color.F_Red, 'Trying to shutdown the computer...', Color.F_Default)
    import sys
    p = 'sys.platform: ' + sys.platform
    print (p)
    log.info(p)
    if not ALLOW_SHUTDOWN:
        p = "shutdown not allowed in this machine"
        print (Color.F_Green, p, Color.F_Default)
        log.warning (p)
        return
    p = 'Going to shutdown in ' + str(s) + ' seconds.'
    log.info(p)
    print (p)
    #(rc, mid) = client.publish(MQTT_PUB + "/result", p)
    (rc, mid) = publicaMqtt(MQTT_PUB + "/result", p)
    status['ups'] = "Shutdown"
    status['smsUPS'] = "off"
    status['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    send_clients_status()
    new_SHUTDOWN_CMD = SHUTDOWN_CMD.copy()
    if IN_HASSIO:
        # inside docker hass, you need anothen command
        new_SHUTDOWN_CMD.insert(0, SHUTDOWN_CMD_HASS)
    if sys.platform == 'darwin':
        new_SHUTDOWN_CMD.insert(0, SHUTDOWN_CMD_DARWIN)
    if sys.platform == 'win32':
        import ctypes
        time.sleep(s)
        user32 = ctypes.WinDLL('user32')
        user32.ExitWindowsEx(0x00000008, 0x00000000)
    else:
        import os
        #time.sleep(s)
        tempoPorVez = int(s/3)
        numeroVezes = s/tempoPorVez
        notifica_n_hass_shutdown(numeroVezes=numeroVezes, tempoPorVez=tempoPorVez)
        for i in range(len(new_SHUTDOWN_CMD)): # SHUTDOWN_CMD
            command = new_SHUTDOWN_CMD[i]  # trying many commands - SHUTDOWN_CMD[i]
            log.info('* Trying...' + command)
            print('* Trying...', Color.F_Blue, command, Color.F_Default)
            os.system(command) # 'sudo shutdown now'
            #ret = os.popen(command).read()
            #log.debug(': ' + str(ret))
            #print(": " + str(ret))


def publicaMqtt(topic, payload):
    "Publica no MQTT atual"
    global gLastMidMqtt
    (rc, mid) = client.publish(topic, payload)
    # print (Color.F_Cyan, topic, Color.F_Default)
    # print (Color.F_Blue, payload, Color.F_Default)
    gLastMidMqtt = mid
    if rc == mqtt.MQTT_ERR_NO_CONN:
        print ("mqtt.MQTT_ERR_NO_CONN")
    if rc == mqtt.MQTT_ERR_SUCCESS:
        # certo, sem erro.
        #print ("mqtt.MQTT_ERR_SUCCESS")
        gLastMidMqtt = mid
    if rc == mqtt.MQTT_ERR_QUEUE_SIZE:
        print ("mqtt.MQTT_ERR_QUEUE_SIZE")
    return rc, mid


def onOff(value, ON = "on", OFF = "off"):
    ''' return a string on / off '''
    v = str(value).upper().replace('-','')
    ret = OFF
    if v == '1': ret = ON
    if v == 'TRUE': ret = ON
    if v == 'ON': ret = ON
    return ret


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global Connected
    global status
    if rc == 0:
        cor = Color.F_Blue 
    else:
        cor = Color.F_Red
    print(cor + "MQTT connected with result code " + str(rc) + Color.F_Default)
    log.debug("MQTT connected with result code " + str(rc))
    if rc == 0:
        print ("Connected to " + MQTT_HOST)
        Connected = True
        status['mqtt'] = "on"
        client.connected_flag = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        if SMSUPS_SERVER and not SMSUPS_CLIENTE:
            log.info("Subscribe Topic: " + MQTT_TOPIC)
            print ("Subscribe Topic: " + MQTT_TOPIC)
            client.subscribe(MQTT_TOPIC)
        else:
            # teste, multiplos topicos
            MQTT_TOPICS = []
            MQTT_TOPICS.append( (MQTT_TOPIC, 0) )  #TODO ver se vai ficar
            MQTT_TOPICS.append( (MQTT_PUB + "/cmd", 0) )
            MQTT_TOPICS.append( (MQTT_PUB + "/json", 0) )
            MQTT_TOPICS.append( (MQTT_PUB + "/batterylevel", 0) )
            MQTT_TOPICS.append( (MQTT_PUB + "/BateriaBaixa", 0) )
            MQTT_TOPICS.append( (MQTT_PUB + "/BateriaEmUso", 0) )
            client.subscribe(MQTT_TOPICS)
            log.info("Subscribe Topics: " + str(MQTT_TOPICS).strip('[]')  )
            print ("Subscribe Topics: " + str(MQTT_TOPICS).strip('[]')  )
        # Mostra clientes
        status['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        send_clients_status()
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
        status['mqtt'] = "off"
        if rc>5: rc=100
        print (str(rc) + str(tp_c[rc]))
        log.error(str(rc) + str(tp_c[rc]))
        # tratar quando for 3 e outros



def send_clients_status():
    ''' send connected clients data '''
    global status
    dadosEnviar = status.copy()
    mqtt_topic = MQTT_PUB + "/clients/" + status['ip']
    dadosEnviar.pop('ip')
    dadosEnviar['UUID'] = UUID
    # dadosEnviar['time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    dadosEnviar['version'] = VERSAO
    dadosEnviar['UPS_NAME_ID'] = UPS_NAME_ID
    dadosEnviar['server'] = onOff(SMSUPS_SERVER)
    dadosEnviar['client'] = onOff(SMSUPS_CLIENTE)
    dadosEnviar['inHass'] = IN_HASSIO
    dadosEnviar['ALLOW_SHUTDOWN'] = ALLOW_SHUTDOWN
    jsonStatus = json.dumps(dadosEnviar)
    (rc, mid) = publicaMqtt(mqtt_topic, jsonStatus)
    return rc


def get_ip(change_dot = False):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.168.1.1', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '0.0.0.1'
    finally:
        s.close()
    if change_dot: IP=IP.replace('.','-')
    return str(IP)

def on_publish(client, userdata, mid):
    # fazer o que aqui? 
    # fazer uma pilha para ver se foi publicado ou não
    # aparentemente só vem aqui, se foi publicado.
    if 1==2:
        print("Published mid: " + str(mid), "last: " + str(gLastMidMqtt))
        if gLastMidMqtt-1 != mid:
            print ("Erro mid:" + str(mid) + " não publicado.")

def on_disconnect(client, userdata, rc):
    global Connected
    global gDevices_enviados
    global status
    Connected = False
    log.info("disconnecting reason  "  +str(rc))
    print("disconnecting reason  "  +str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
    gDevices_enviados['b'] = False # Force sending again
    status['mqtt'] = "off"
    # mostra cliente desconectado
    try:
        send_clients_status()
    except Exception as e:
        mostraErro(e, 30, "on_disconnect")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global gNoBreakLast
    try:
        res = json.loads(msg.payload)
    except Exception as e:
        if e.__class__.__name__ == 'JSONDecodeError':
            msg_p = msg.payload
            msg_p = msg_p.decode()
            msg_p = msg_p.replace("'",'"')
            #res = json.loads(msg_p)
            res = msg_p
        else:
            mostraErro(e, 40, "on_message")

    # log.debug("on_message: " + msg.topic + " " + str(msg.payload))
    soCliente = SMSUPS_CLIENTE and not SMSUPS_SERVER
    if msg.topic == MQTT_PUB + "/BateriaEmUso":
        if soCliente:
            BateriaEmUso = msg.payload.decode()
            gNoBreakLast['BateriaEmUso'] = str2bool(BateriaEmUso)
        return None
    if msg.topic == MQTT_PUB + "/BateriaBaixa":
        if soCliente:
            BateriaBaixa = msg.payload.decode()
            gNoBreakLast['BateriaBaixa'] = str2bool(BateriaBaixa)
        return None
    if msg.topic == MQTT_PUB + "/inputVac":
        if soCliente:
            inputVac = msg.payload.decode()
            gNoBreakLast['inputVac'] = int(inputVac)
        return None

    if msg.topic == MQTT_PUB + "/batterylevel":
        # nível bateria mudou.
        client_bat_level = float(msg.payload.decode())

        BateriaBaixa = gNoBreakLast['BateriaBaixa']
        BateriaEmUso = gNoBreakLast['BateriaEmUso']
        inputVac = int( gNoBreakLast['inputVac'] )

        checkBatteryLevel2(client_bat_level, BateriaBaixa, BateriaBaixa, inputVac, False)
        return None
    if msg.topic == MQTT_PUB + "/json":
        # mudou o json
        if SMSUPS_CLIENTE and not SMSUPS_SERVER:
            # guarda as informações
            gNoBreakLast = res.copy()

        client_bat_level = float(res.get('batterylevel'))
        BateriaBaixa = res.get('BateriaBaixa')
        BateriaEmUso = res.get('BateriaEmUso')
        inputVac = int( res.get('inputVac') )
        checkBatteryLevel2(client_bat_level, BateriaBaixa, BateriaEmUso, inputVac, False)
        if soCliente:
            # seta os dados de bateria
            gNoBreakLast['BateriaBaixa'] = str2bool(BateriaBaixa)
            gNoBreakLast['BateriaEmUso'] = str2bool(BateriaEmUso)
            gNoBreakLast['inputVac'] = inputVac
        return None

    if not type(res) is list and not type(res) is dict:
        # não é uma lista - sair
        if str(res).upper().find('CMD') == -1:
            print ("Erro de Comando - é um " + str(type(res)) + " " + str(res) )
            log.warning ("Erro de Comando - é um " + str(type(res)) + str(res) )
            return None
        elif type(res) is str:
            res = json.loads(res)

    if not "cmd" in res.keys():
        # não tem o comando certo. Sair
        print ("Comando cmd não encontrado")
        log.warning ("Comando cmd não encontrad")
        return None
    v=res['cmd'].upper()
    if v=='T':
        ret = send_command("Test",cmd['T'], sendQ=True)
        (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=='TN':
        val = res['val']
        if val.isnumeric():
            val = int(val)
            comando = tempo2hexCMD(val)
            ret = send_command("Test n", comando, sendQ=True)  # teste N minutes
            (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="M":
        ret = send_command("Beep",cmd['M'], sendQ=True)
        (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="C":
        ret = send_command("CancelShutdown",cmd['C'], sendQ=True)  # cancela shutdown ou reestore
        (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="D":
        ret = send_command("Cancel",cmd['D'], sendQ=True)  # cancela Testes
        (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="L":
        ret = send_command("TestLow",cmd['L'], sendQ=True)   # testa até low battery
        (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="RAW":
        # envia comando como recebido
        ret = send_command("Raw",res['val'])
        if len(ret)>0:
            log.debug("publish: " + MQTT_PUB + "/result : " + str(ret))
            (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
    elif v=="CMD":
        # envia comando e inclui checksum
        if len(res['val'])!=0:
            comando = montaCmd(res['val'])
            ret = send_command("CMD", comando)
            if len(ret)>0:
                log.debug("publish: " + MQTT_PUB + "/result : " + str(ret))
                (rc, mid) = publicaMqtt(MQTT_PUB + "/result", str(ret))
                ret = ""
        else:
            log.debug("publish: " + MQTT_PUB + "/result : Invalid command")
            (rc, mid) = publicaMqtt(MQTT_PUB + "/result", "Invalid command")
    elif v=="SHUTDOWN":
        # call shutdonw commands
        shutdown_computer()
        log.warning ( " I can't shutdown the computer" )
        print(Color.F_Cyan, " I can't shutdown the computer", Color.F_Default )
        return False
    
    if len(ret)>5:
        queryQ(ret)
    else:
        queryQ()


def send_command(cmd_name, cmd_string, sendQ = False):
    ''' envia um comando para o nobreak '''
    global serialOk
    global status
    respHex = ""
    comando = cmd_string
    if cmd_name != "query":
        log.debug ("cmd:" + cmd_name + " / str: " + comando + " / Q: " + str(sendQ))
    if serialOk:
        if sendQ: comando = comando + ' ' + cmd['Q']  # adiciona o Q.
        cmd_bytes = bytearray.fromhex(comando)
        try:
            for cmd_byte in cmd_bytes:
                hex_byte = ("{0:02x}".format(cmd_byte))
                ser.write(bytearray.fromhex(hex_byte))
                time.sleep(.100)
            response = ser.read(32)
            respHex = binascii.hexlify(bytearray(response))
        except serial.SerialException:
            status['serial'] = 'off'
            serialOk = ser.is_open()
            respHex = ""
        except Exception as e:
            status['serial'] = 'off'
            mostraErro(e,30,"send_command")
            serialOk = ser.is_open()
            respHex = ""
        if cmd_name != "query":  # evita muitas gravações no log
            log.debug ("response: " + str(respHex))
    else:
        log.warning('send-cmd - serial not ok')
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
    noBreak['noData']=False
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
        noBreak['noData']=True
    noBreak['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    noBreak['lastinputVac'] = toINT16(lista[1])/10
    noBreak['inputVac'] = toINT16(lista[2])/10
    noBreak['outputVac'] = toINT16(lista[3])/10
    noBreak['outputPower'] = toINT16(lista[4])/10
    # TODO: melhorar isto.
    noBreak['powerNow'] = int(SMSUPS_FULL_POWER) * int(float(str(noBreak['outputPower'])))/100
    noBreak['outputHz'] = toINT16(lista[5])/10
    noBreak['batterylevel'] = toINT16(lista[6])/10
    noBreak['temperatureC'] = toINT16(lista[7])/10
    bi = "{0:08b}".format(toINT16(lista[8]))
    # bj = "{0:08b}".format(toINT16(lista[9]))
    noBreak['BeepLigado'] = onOff(bi[7])     # Beep Ligado
    noBreak['ShutdownAtivo'] = onOff(bi[6])  # ShutdownAtivo
    noBreak['TesteAtivo'] = onOff(bi[5])     # teste ativo
    noBreak['UpsOk'] = onOff(bi[4])          # upsOK / Vcc na saída
    noBreak['Boost'] = onOff(bi[3])          # Boost / Potência de Saída Elevada
    noBreak['ByPass'] = onOff(bi[2])         # byPass
    noBreak['BateriaBaixa'] = onOff(bi[1])   # Bateria Baixa / Falha de Bateria
    noBreak['BateriaEmUso'] = onOff(bi[0])  # Bateria Ligada / em uso
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


def date_diff_in_Seconds(dt2, dt1):
    # Get time diference in seconds
    # not tested for many days.
  timedelta = dt2 - dt1
  return timedelta.days * 24 * 3600 + timedelta.seconds

def tempo2hexCMD(i):
    '''  Converte um int para hex para ser enviado '''
    if not type(i) is int:
        log.error ('i must be a integer.') 
        i = 0
    if i > 3600:
        log.warning ('tempo2hex: Valor de i > 3600. i=' + i)
        i = 3600
    ret = "000000" + hex(i)[2:]
    ret = ret[-4:].upper()
    ret = ret[0:2] + " " + ret[2:5]
    ret = cmd['T'][0:2] + " " + ret + "  00 00"
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
        #if key == "time" or key == 'publish_time':
        #    print (Color.B_LightGray, topi, Color.B_Default)
        #    print (Color.F_LightRed, val, Color.F_Default)
        #    print (Color.F_LightRed, str(val), Color.F_Default)
        (rc, mid) = publicaMqtt(topi, str(val))
        
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
    log.debug ("UPS Info: " + 
        noBreakInfo['name'] + " / " + 
        noBreakInfo['info'])
    if noBreakInfo['name'][-1:] == '\r': noBreakInfo['name'] = noBreakInfo['name'][0:-1]
    if noBreakInfo['info'][-1:] == '\r': noBreakInfo['info'] = noBreakInfo['info'][0:-1]
    if len(noBreakInfo['info'])>=1:
        if noBreakInfo['info'][0] == ';':
            noBreakInfo['info'] = noBreakInfo['info'][1:]
    log.debug ("UPS Info: " + 
        noBreakInfo['name'] + " / " + 
        noBreakInfo['info'])


def publicaDados(upsData):
    # publica dados no MQTT
    global status
    global gMqttEnviado
    if ENVIA_JSON:
        upsData.update(noBreakInfo)  # junta outros dados
        jsonUPS = json.dumps(upsData)
        (rc, mid) = publicaMqtt(MQTT_PUB + "/json", jsonUPS)
        gMqttEnviado['b'] = True
        gMqttEnviado['t'] = datetime.now()
    if ENVIA_MUITOS:
        publish_many(MQTT_PUB, upsData)
        gMqttEnviado['b'] = True
        gMqttEnviado['t'] = datetime.now()
    if ENVIA_JSON or ENVIA_HASS or ENVIA_MUITOS:
        if status['serial'] == 'open' and status['ups'] == 'Connected' and status['mqtt'] == 'on': 
            status[APP_NAME] = "on"
        else:
            status[APP_NAME] = "off"
        send_clients_status()

def pegaEnv(env):
    ret = ""
    try:
        ret = os.environ[env]
    except:
        ret = ""
    return ret

def queryQ(raw = ""):
    ''' get ups data and publish'''
    global status
    global statusLast
    global gMqttEnviado
    global gNoBreakLast

    if raw == "":
        x = send_command("query",cmd['Q'])
    else:
        x = raw
    lista_dados = trataRetorno(x)
    try:
        upsData = dadosNoBreak(lista_dados)
    except Exception as e:
        mostraErro(e)
        log.debug('lista_dados: ' + str(lista_dados))
        log.debug('x: ' + str(x))
        log.debug('deu erro queryQ')
        exit()
    if upsData['noData']:
        printC(Color.B_Red, 'no UPS Data')
        exit()
    if gNoBreakLast['publish_time'] == '': gNoBreakLast = upsData.copy()
    if False: # ECHO
        print ('---------')
        print (x)
        mostra_dados(upsData)
    if SMSUPS_SERVER:
        checkBatteryLevel(upsData)  # check battery level
    if Connected and SMSUPS_SERVER:
        time_dif = date_diff_in_Seconds(datetime.now(), gMqttEnviado['t'])
        if  time_dif > INTERVALO_MQTT:
            gMqttEnviado['b'] = False
        dataChanged = checkDataChange(upsData, gNoBreakLast)
        if len(dataChanged) != 0:
            gMqttEnviado['b'] = False
            gNoBreakLast = upsData.copy()
        if gMqttEnviado['b']:
            dataChanged = checkDataChange(status, statusLast, status)
            if len(dataChanged) != 0:
                gMqttEnviado['b'] = False
                statusLast = status.copy()
        if not gMqttEnviado['b']:
            # log.debug('Publica Dados')
            publicaDados(upsData)
    return upsData

def checkDataChange(now, last, tags = "SERIAL_CHECK_ALWAYS"):
    '''  Verifica se os parametros alteraram '''
    if tags == "SERIAL_CHECK_ALWAYS": tags = SERIAL_CHECK_ALWAYS.copy()
    ret = list()
    for i in tags:
        itemN = now[i] if i in now else "1"
        itemL = last[i] if i in last else "2"
        #if i in now: itemN = now[i] if True else "1"
        #if i in last: itemL = last[i] if True else "0"
        if itemN != itemL: ret.append(i)
    return ret

def checkBatteryLevel(upsData):
    ''' check if battery still enough '''
    global gBattery
    bat = int(upsData['batterylevel'])
    BateriaEmUso = upsData['BateriaEmUso']
    if bat < UPS_BATERY_LEVEL and bat!=0 and not upsData['noData']:
        # bateria acabando.
        checkBatteryLevel2(bat, upsData['BateriaBaixa'], BateriaEmUso, int(upsData['inputVac'], upsData['noData']) )
        #if upsData['BateriaBaixa']=="on" or upsData['BateriaEmUso']=='on': # evita shutdown no pico de volta
        #    client.publish(MQTT_PUB + "/cmd", MQTT_CMD_SHUTDOWN )
    if IN_HASSIO:
        msg = ""
        tit = ""
        id = HASS_DEFAULT_NOENERGY_ID
        if bat == 0: bat = 1
        if str2bool(BateriaEmUso):
            if gBattery['time'] == 0: 
                gBattery['time'] = datetime.now()
                gBattery['batterylevel'] = bat
            else:
                time_dif = date_diff_in_Seconds(datetime.now(), gBattery['time'])
                bat_dif = bat - gBattery['batterylevel']
                batConsumo = bat_dif / time_dif
                print("batConsumo: ", batConsumo)
                if batConsumo != 0:
                    batLeft = int((bat - UPS_BATERY_LEVEL) / batConsumo)
                else:
                    batLeft = int((bat - UPS_BATERY_LEVEL))
                id = HASS_DEFAULT_NOENERGY_ID
                tit = "No energy!"
                msg = "".join(("Running without energy for **" + str(timedelta(seconds=time_dif)) + " seconds.**",
                    "<BR><BR>" + "Battery level: **" + str(bat) + " %" + "**",
                    "<BR>" + "Shutdown battery level: **" + str(UPS_BATERY_LEVEL) + " %" + "**",
                    "<BR>" + "Estimated shutdown time in **" + str(timedelta(seconds=batLeft)) + "**"))
                if upsData['noData']:
                    tit = "No UPS Data!"
                    msg = "".join(("No UPS data for **" + str(timedelta(seconds=time_dif)) + " seconds.**",
                    "<BR><BR>" + "Please check seria/usb port: " + porta_atual))
        else:
            if not gBattery['time']== 0:
                time_dif = date_diff_in_Seconds(datetime.now(), gBattery['time'])
                id = int(HASS_DEFAULT_NOENERGY_ID) + 1
                tit = "Energy returned!"
                msg = "".join(("Now battery is charging.",
                    "<BR><BR>" + "Battery level: **" + str(bat) + " %" + "**",
                    "<BR>" + "I ran without power for **" + str(timedelta(seconds=time_dif)) + " seconds.**"))
                gBattery['time'] = 0 # zera contador de tempo de uso da bateria.
                gBattery['batterylevel'] = 1
        if not msg == "":
            str_hora = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            msg_i = "**" + UPS_NAME_ID + "**<BR>"
            nova_msg = "".join((msg_i, msg, '<BR><BR>*', str_hora, "*<BR>*<sub><sup>by ", MANUFACTURER, "</sup></sub>*"))
            titulo = APP_NAME + " - " + tit 
            notifica_hass(titulo = titulo, msg = nova_msg, id = id)


def checkBatteryLevel2(batterylevel, bateriaBaixa, bateriaEmUso, inputVac, upsNoData):
    ''' Verifica o nível de bateria e chama o shutdown caso necessário '''
    bat = batterylevel
    if bat < UPS_BATERY_LEVEL and bat!=0 and not upsNoData:
        # bateria acabando.
        log.warning ("Battery low " + str(bat) + "%")
        log.warning ("Input Vac " + str(inputVac) )
        print (Color.B_Red, Color.F_White, "Battery low " + str(bat) + "%", Color.B_Default, Color.F_Default)
        if str2bool(bateriaBaixa) or str2bool(bateriaEmUso): # evita shutdown no pico de volta
            if inputVac < UPS_INPUT_VAC:
                log.warning ("Sending shutdown command")
                print ("Sending shutdown command")
                # TODO colocar o horario
                mqqt_cmd_copy = Template(MQTT_CMD_SHUTDOWN)
                mqqt_cmd_copy = mqqt_cmd_copy.safe_substitute(publish_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                (rc, mid) = publicaMqtt(MQTT_PUB + "/cmd", mqqt_cmd_copy ) # 


def json_remove_vazio(strJson):
    ''' remove linhas / elementos vazios de uma string Json '''
    strJson.replace("\n","")
    try:
        dados = json.loads(strJson)  # converte string para dict
    except Exception as e:
        if e.__class__.__name__ == 'JSONDecodeError':
            log.warning ("erro json.load: " + strJson)
        else:
            mostraErro(e, 40, "on_message")
    cp_dados = json.loads(strJson) # cria uma copia
    for k,v in dados.items():
        if len(v) == 0:
            cp_dados.pop(k)  # remove vazio
    return json.dumps(cp_dados) # converte dict para json


def monta_publica_topico(component, sDict, varComuns):
    ''' monta e envia topico '''
    key_todos = sDict['todos']
    newDict = sDict.copy()
    newDict.pop('todos')
    for key,dic in newDict.items():
        # print(key,dic)
        if key[:1] != '#':
            varComuns['uniq_id']=varComuns['identifiers'] + "_" + key
            if not('val_tpl' in dic):
                dic['val_tpl'] = dic['name']
            dic['name'] = varComuns['uniq_id']
            dic['device_dict'] = device_dict
            dic['publish_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            dic['expire_after'] = INTERVALO_EXPIRE # quando deve expirar
            dados = Template(json_hass[component]) # sensor
            dados = Template(dados.safe_substitute(dic))
            dados = Template(dados.safe_substitute(varComuns)) # faz ultimas substituições
            dados = dados.safe_substitute(key_todos) # remove os não substituidos.
            topico = MQTT_HASS + "/" + component + "/" + NODE_ID + "/" + varComuns['uniq_id'] + "/config"
            # print(topico)
            # print(dados)
            dados = json_remove_vazio(dados)
            (rc, mid) = publicaMqtt(topico, dados)
            # print ("rc: ", rc)


def send_hass():
    ''' Envia parametros para incluir device no hass.io '''
    global sensor_dic
    global gDevices_enviados

    # var comuns
    varComuns = {'sw_version': VERSAO,
                 'model': noBreakInfo['info'],
                 'manufacturer': MANUFACTURER,
                 'device_name': noBreakInfo['name'],
                 'identifiers': UPS_NAME + "_" + UPS_ID,
                 'via_device': VIA_DEVICE,
                 'ups_id': UPS_NAME_ID,
                 'uniq_id': UPS_ID}
    if DEVELOPERS_MODE:
        log.debug('Sensor_dic: ' + str(len(sensor_dic)))
    if len(sensor_dic) == 0:
        for k in json_hass.items():
            json_file_path = k[0] + '.json'
            if IN_HASSIO:
                json_file_path = '/' + json_file_path  # to run on HASS.IO
            if not os.path.isfile(json_file_path):
                log.error(json_file_path + " not found!")
            json_file = open(json_file_path)
            json_str = json_file.read()
            sensor_dic[k[0]] = json.loads(json_str)

    for k in sensor_dic.items():
        # print('Componente:' + k[0])
        monta_publica_topico(k[0], sensor_dic[k[0]], varComuns)

    gDevices_enviados['b'] = True
    gDevices_enviados['t'] = datetime.now()
    if DEVELOPERS_MODE:
        log.debug('Hass Sended')

def serialExist(serialPort, imprime=True):
    ''' verifica se uma porta serial existe no sistema - linux'''
    osEnv = dl.dadosOS()
    ret = False
    if osEnv['os.name'] == 'posix':
        import os
        ret = os.path.exists(serialPort)
    else:
        dl.printC(Color.B_Magenta, 'Error - Not linux system')
        exit()
    if imprime:
        if ret:  
            dl.printC(Color.B_Blue, ''.join(serialPort)+' exist')
        else:
            dl.printC(Color.B_Red, ''.join(serialPort)+' not exist')
    return ret

def abre_serial():
    ''' abre a porta serial '''
    global ser
    global serialOk
    global status
    global porta_atual
    porta_ser = PORTA[porta_atual].strip()
    # lista as portas USB/serial
    #try:
    #    myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
    #    printC(Color.B_Green, 'COMM Ports:')
    #    print (myports)
    #except Exception as e:
    #    mostraErro(e, 40, "AbreSerial-ListaSerial")
    try:
        ser = serial.Serial(porta_ser,
            baudrate=2400,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = SERIAL_PORT_TIMEOUT)  # era 1
        print ("Porta: " + porta_ser + " - " + str(ser.isOpen()))
        log.info ("Port " + porta_ser + " - is open: " + str(ser.isOpen()))
        printC (Color.F_Green, 'portstr: ' + ser.portstr)
        serialOk = ser.isOpen() # True
        status['serial'] = "open"
    except Exception as e:
        # printC (Color.F_Red, 'portstr: ' + ser.portstr)  não está aberta a porta...
        if e.__class__.__name__ == 'SerialException':
            print (Color.F_Red + "I was unable to open the serial port ", porta_ser, Color.F_Default)
            log.warning ("I was unable to open the serial port " + porta_ser) 
        else:
            mostraErro(e, 40, "AbreSerial")
        status['serial'] = 'off'
        serialOk = False
        # verifica outras portas se for servidor
        if SMSUPS_SERVER:
            porta_atual+=1   # add 1
            if porta_atual > len(PORTA)-1:
                porta_atual = 0
            else:
                # tenta abrir a próxima porta
                abre_serial()
    return serialOk

def mqttStart():
    ''' Start MQTT '''
    global client
    global clientOk
    # MQTT Start
    client = mqtt.Client()
    log.info("Starting MQTT " + MQTT_HOST)
    log.debug("mqttStart MQTT_PASSWORD: " + str(MQTT_PASSWORD))
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    try:
        clientOk = True
        rc = client.connect(MQTT_HOST, 1883, 60)

    except Exception as e:  # OSError
        if e.__class__.__name__ == 'OSError':
            clientOk = False
            log.warning("Can't start MQTT")
            print (Color.F_Red + "Can't start MQTT" + Color.F_Default)  # e.errno = 51 -  'Network is unreachable'
            mostraErro(e,20, "MQTT Start")
        else:
            clientOk = False
            mostraErro(e,30, "MQTT Start")
    if clientOk:  client.loop_start()  # start the loop


def iniciaLoggerStdout():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def iniciaLogger():
    log = logging.getLogger('smsUPS')
    erroDif = False
    try:
        hdlr = logging.FileHandler(LOG_FILE)
    except PermissionError:  # caso não consiga abrir
        hdlr = logging.FileHandler('./smsUPS.log')
    except Exception as e:
        erroDif = e
    finally:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        log.addHandler(hdlr) 
        log.setLevel(LOG_LEVEL)
    if erroDif != False:
        # different error
        mostraErro(e, 20, 'Open LOG_FILE')
    if hdlr.baseFilename != LOG_FILE:
        print ('LOG file: ', hdlr.baseFilename)
        log.debug ('LOG file: ' + hdlr.baseFilename)
    return log

def notifica_hass (titulo, msg, id = False):
    global Long_lived_access_token
    if not IN_HASSIO: return None
    if type(id) is str:
        id = int(id)
    if IN_HASSIO and len(Long_lived_access_token) > 0:
        command = Template( HASS_CMD_NOTIFY ) 
        outro = ""
        if int(id) > 1:
            outro = ', "notification_id": "' + str(id) + '"'
        substitui = {
            'Long_lived_access_token':Long_lived_access_token,
            'message': msg,
            'titulo': titulo,
            'outro': outro} 
        command = command.substitute(substitui)
        ## ENVIA COMANDO
        ret = os.system(command)
        if ret != 0:
            print('* Tried: ', Color.F_Blue, command, Color.F_Default)
        # print (Color.F_Cyan, 'Resultado: ' + str(ret), Color.F_Default)


def publicaDadosWeb(sensor_dic):
    # publica dados na web por meio do webserver via JSON
    jsonx = publicaDados(sensor_dic)
    # add new data
    json_load = json.loads(jsonx)
    #json_load['last_time'] = gEnvios['last_time']  
    #json_load['load_cnt'] = gEnvios['load_cnt']
    #json_load['load_time'] = gEnvios['load_time']
    json_x = json.dumps(json_load)
    return json_x


def publicaDados(upsData):
    # publica dados no MQTT
    global status
    global gMqttEnviado
    jsonUPS = json.dumps(upsData)
    (rc, mid) = publicaMqtt(MQTT_PUB + "/json", jsonUPS)
    gMqttEnviado['b'] = True
    gMqttEnviado['t'] = datetime.now()
    print (Color.F_Blue + "Dados UPS Publicados..." + Color.F_Default + str(datetime.now()))
    if status['mqtt'] == 'on': 
        status[APP_NAME] = "on"
    else:
        status[APP_NAME] = "off"
    send_clients_status()
    return jsonUPS



# RODA O APP WEB
def iniciaWebServerB(Conf):
    ''' inicia o webserver '''
    printC(Color.B_Blue,'Port: ' + str(os.getenv('PORT', 4443)))
    printC(Color.B_Blue,'Host: ' + str(os.getenv('IP', '0.0.0.0')))
    webserver.app.run(debug=True, host="0.0.0.0", threaded=True)
    if 1==0:
        #TODO: arrumar
        try:
            if dl.IN_HASSIO():
                webserver.app.run(debug=True,
                    host="0.0.0.0",
                    threaded=True
                )
            else:
                webserver.app.run(debug=True,
                    host=os.getenv('IP', '0.0.0.0'), 
                    port=int(os.getenv('PORT', 5005))
                )
        except Exception as e:
            printC(Color.F_Red, "Can't start Webserver")
            mostraErro(e, 30, 'WARNING')
            pass


def iniciaWebServer():
    ''' inicia o webserver '''
    printC (Color.B_Magenta, "WEB SERVER Starting ...")

    path_index = comum.PATH_TEMPLATE
    if dl.IN_HASSIO():
        path_index = comum.PATH_TEMPLATE_HAS

    bl_existe_index = os.path.isfile(path_index + '/index.html')
    if not bl_existe_index:
        ''' não existe o index '''
        printC (Color.B_Red, "Index not found. I can't start webserver. ")
        arr = os.listdir(path_index)
        printC(Color.F_Magenta, path_index)
        print(arr)
    else:
        # existe index
        p = multiprocessing.Process(target=iniciaWebServerB, args=({"Something":"SomethingElese"},))
        p.start()




# APP START - Inicio

print (Color.B_Blue + "********** " + MANUFACTURER + " " + APP_NAME + " v." + VERSAO + Color.B_Default)
print (Color.B_Green + "Starting up... " + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + Color.B_Default)

# hass.io token
IN_HASSIO = ( pegaEnv('HASSIO_TOKEN') != "" and PATH_ROOT == "/data")


# version check
if int(dl.version()) < int(version_expected['dmslibs']):
    printC (Color.B_Red, "Wrong dmslibs version! ")
    printC (Color.F_Blue, "Current: " + dl.version() )
    printC (Color.F_Blue, "Expected: " + version_expected['dmslibs'] )


#LOG
if IN_HASSIO:
    #log = iniciaLoggerStdout()
    log = dl.inicia_log(logFile='/var/tmp/hass.hoymiles.log', logName='hass.hoymiles', stdOut=True)
else:
    #log = iniciaLogger()
    log = dl.inicia_log(logFile='/var/tmp/hass.hoymiles.log', logName='hass.hoymiles', stdOut=False)

log.debug("********** " + MANUFACTURER + " " + APP_NAME + " v." + VERSAO)
log.debug("Starting up...")

print ("Path: " + PATH_ROOT)
log.debug ("Path: " + PATH_ROOT)

# print (os.environ)

print("hassio_token:" + pegaEnv('HASSIO_TOKEN'))
log.debug ("Running inside HASSIO " + str(IN_HASSIO))

log.debug ("env1:" + pegaEnv("PORTA"))

get_secrets()
log.setLevel(LOG_LEVEL)
status['ip'] = get_ip()

log.debug ("PORTA secrets: " + ''.join(PORTA))

# Pega dados do hass, se estiver nele.


if DEVELOPERS_MODE:
    print (Color.B_Red, "DEVELOPERS_MODE", Color.B_Default)
else:
    print (Color.B_Blue, "NORMAL MODE", Color.B_Default)

if IN_HASSIO:
    print (Color.B_Blue, "IN HASS.IO", Color.B_Default)
    substitui_secrets()
    log.debug ("PORTA substitui: " + ''.join(PORTA))
    if USE_SECRETS:
        # se for para usar o secrets, carrega ele novamente.
        get_secrets()
    if DEFAULT_MQTT_PASS == MQTT_PASSWORD:
        log.warning ("YOU SHOUD CHANGE DE DEFAULT MQTT PASSWORD!")
        print (Color.F_Red + "YOU SHOUD CHANGE DE DEFAULT MQTT PASSWORD!" + Color.F_Default)

log.debug("SMSUPS_SERVER: " + str(SMSUPS_SERVER))
log.debug("SMSUPS_CLIENTE: " + str(SMSUPS_CLIENTE))
log.debug("MQTT_HOST: " + str(MQTT_HOST))
log.debug("IP: " + status['ip'])
print ("SMSUPS_SERVER: " + Color.B_Green + str(SMSUPS_SERVER) + Color.B_Default)
print ("SMSUPS_CLIENTE: " + Color.B_Green + str(SMSUPS_CLIENTE) + Color.B_Default)
print ("IP: " + Color.F_Magenta + status['ip'] + Color.F_Default)
print ("UPS_ID: " + Color.B_LightYellow + str(UPS_ID) + Color.B_Default)
print ("UPS_NAME: " + Color.B_LightYellow + str(UPS_NAME) + Color.B_Default)
print ("UPS_NAME_ID: " + Color.B_LightYellow + str(UPS_NAME_ID) + Color.B_Default)
print ("ALLOW_SHUTDOWN: " + Color.B_Red + str(ALLOW_SHUTDOWN) + Color.B_Default)
# print ("Long_lived_access_token: " + Color.F_Magenta + Long_lived_access_token + Color.F_Default)

# info
try:
    printC(Color.F_Blue, 'Getting OS Data')
    osEnv = os.environ
    log.info("os.name: " + str(os.name))
    log.info("os.getlogin: " + str(os.getlogin()))
    log.info("os.uname: " + str(os.uname()))
    log.info("whoami: " + str(os.popen('whoami').read()))
except Exception as e:
    printC(Color.F_Red, "Can't get OS Data")
    mostraErro(e, 10, 'info')
# if 'VIRTUAL_ENV' in osEnv
# log.info("VIRTUAL_ENV: " + osEnv['VIRTUAL_ENV'])

# pega novamente os dados do SO (teste)
dl.dadosOS() 

# verifica a porta serial
serialExist('/dev/ttyUSB0')

# signals monitor
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)

while not Connected:
    mqttStart()
    time.sleep(1)  # wait for connection
    if not clientOk:
        time.sleep(240)

serialOk = False

if not serialOk:
    if SMSUPS_SERVER: serialOk = abre_serial()

# Time entre a conexao serial e o tempo para escrever (enviar algo)
time.sleep(1.8) # Entre 1.5s a 2s

if SMSUPS_SERVER:
    getNoBreakInfo()
    if ENVIA_HASS:
        send_hass()

if WEB_SERVER:  # se tiver webserver, inicia o web server
    printC(Color.F_LightBlue, "Web server outorder")
    # iniciaWebServer()


printC(Color.B_LightCyan, 'Loop start!')
# loop start
while True:
    if SMSUPS_SERVER:  # só se for servidor
        upsData = queryQ()  # Get UPS data
        if WEB_SERVER:  # se tiver webserver, inicia o web server
            try:
                dl.writeJsonFile(FILE_COMM, upsData)
            except Exception as e:
                mostraErro(e, 30, "Webserver write json")
        if ENVIA_HASS:   # verifica se vai enviar cabeçalho para HASS
            if (not gDevices_enviados['b']) and Connected and SMSUPS_SERVER:
                send_hass
            elif Connected and SMSUPS_SERVER:
                time_dif = date_diff_in_Seconds(datetime.now(), \
                  gDevices_enviados['t'])
                if time_dif > INTERVALO_HASS:
                    gDevices_enviados['b'] = False
                    send_hass() 
        if not serialOk:
            serialOk = abre_serial()
        if not clientOk: mqttStart()  # tenta client mqqt novamente.
    time.sleep(INTERVALO_SERIAL) # dá um tempo


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
    09 - 0x22 (")	- 0X  DD - outputPower
	10 - 0x02		- 0XEE   -
	11 - 0x58 (X)	- 0X  EE - outputHz
	12 - 0x03		- 0XFF   -
	13 - 0xe8		- 0X  FF - batterylevel
	14 - 0x01		- 0XGG   -
	15 - 0x7c (|)	- 0X  GG - temperatureC
	16 - 0x29 ())	- HH     - State bits (beepon, shutdown, test, upsok, boost, onacpower, lowbattery, onbattery)
	17 - 0x01		- ??	 - checksum  ???
	18 - 0x0d		- Final da resposta

 
    whereis Potência de Saída ???

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
BateriaEmUso
'''
