__author__ = 'dmslabs'

import serial
import time
import struct
import binascii
import os


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

''' 8-bit checksum 0x100 '''
def chk(st):
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

''' Para Int 16 '''
def toINT16(valorHex):
    ret = int(valorHex,16)
    return ret

''' Para as variaveis certas '''
def dadosNoBreak(lista):
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

''' mostra os dados na tela '''
def mostra_dados(dic):
    for k,v in dic.items():
        print(k,v)


def test(raw):
    lista_dados = trataRetorno(raw)
    ret = dadosNoBreak(lista_dados)
    print (raw)
    mostra_dados(ret)

def montaCmd(c1, c2):
    st = c1 + ' ' + c2
    check = chk(st)
    check = check.replace("0x","")
    ret = st + ' ' + check +  ' ' +  CR 
    return ret



# dados

CR = '0D'

readOut = 0   
montaCmd('47','ff ff ff ff')

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

print("** SMS UPS v.0.1")


porta = '/dev/tty.usbserial-1440' # '/dev/ttyUSB0'

try:
    ser = serial.Serial(porta,
        baudrate=2400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout = 1) # ttyACM1 for Arduino board
except:
    ser = ""

# Time entre a conexao serial e o tempo para escrever (enviar algo)
time.sleep(1.8) # Entre 1.5s a 2s




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



               

                                    

print ("Starting up...")
# print (ser.isOpen())


test("3d 00 00 00 00 04 7d 00 00 02 58 03 66 01 38 89 bd 0d")

print ('-----')
test("3d 00 00 08 e0 04 7d 00 00 02 58 03 e8 01 bd 09 4e 0d")
print ( '  ----   ')
test("3d 00 00 08 e9 04 86 00 00 02 58 03 e8 01 bd 09 3c 0d")

'''
Falha de Bateria - 0 
Carga da Bateria - 1
Rede Elétrica - 1
Potência de Saída Elevada - 0 
Teste de Bateria - 0 
Alerta 24h - 1
'''

while 1==2:
    x = send_command("query",cmd[1])
    lista_dados = trataRetorno(x)
    ret = dadosNoBreak(lista_dados)
    # os.system('cls' if os.name == 'nt' else 'clear')
    print ('---------')
    print (x)
    mostra_dados(ret)
    time.sleep(5)

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

time.sleep(2)
ser.close()