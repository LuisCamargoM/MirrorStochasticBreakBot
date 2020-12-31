#!/usr/bin/python3
from iqoptionapi.stable_api import IQ_Option
import pandas as pd
from candlestick import candlestick
from datetime import datetime,timedelta
import time, json
from time import strftime
import csv
import uuid
import chuckTelegramConfig as config_tel
import signal
import logging
import os
from dateutil import tz
import sys
import telegram


#Retorna String com data e hora do 'x'
def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))
    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)

arq = timestamp_converter(time.time())
fileName = (str(path)+'/Logs/'+arq+'.txt').replace('\\',',')
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S ',filename=fileName,level=logging.INFO)

def writeLog(info):
    logging.info(info)

#####################
###### CONEXÃO ######
#####################
API = IQ_Option('y_akousa@hotmail.com','Luis2021_!')
API.connect()
API.change_balance('REAL')

while True:
    if API.check_connect() == False:        
        writeLog('Erro ao se conectar!')    
        API.connect()    
    else:
        writeLog('Conectado com sucesso! '+str(os.getpid()))
        break

#####################
##### VARIAVEIS #####
#####################
#TELEGRAM
my_token = config_tel.token
chat_id = config_tel.chat_id

#LIST
signList = [] 
contSignal = [0]
check = []

#TIMEFRAMES
M1 = [1,60]
M2 = [2,120]
M5 = [5,300]
M15 = [15,900]
M30 = [30,1800]

#DV
dvFifth = 5
dvSixth = 7
dvEighth = 8

#tam
tamFifth = 11
tamSixth = 13
tamEighth = 15

#####################################################
############### FUNÇOES AUXILIARES ##################
#####################################################
def getPastCandles(par,opTime,qtd,tm):                  
    vela = API.get_candles(par,opTime,qtd,tm)
    if vela is None:
        return 'None'
    else:    
        return vela

def getCorrectHour():
    tmp = timestamp_converter(API.get_server_timestamp())[11:19]
    a = int(tmp[6:8]) + 1
    b = tmp[0:6]
    tmp = str(b + str(a))
    return tmp

def getActualCandleColor(x,pos):
    # closeAnt = x[pos-1]['close']
    close = x[pos]['close']    
    open = x[pos]['open']
    dif = close - open
    if (dif == 0):
        return 'Doji' 
    else:
        if (dif > 0):
            return 'Green'
        else:
            return 'Red' 

def getNextTime(tm,min):
    t = datetime.strptime(str(tm),"%Y-%m-%d %H:%M:%S")
    delta = t + timedelta(minutes=min)
    return str(delta)

def getTimestamp(ts):
    element = datetime.strptime(str(ts),"%Y-%m-%d %H:%M:%S") 
    tuple = element.timetuple() 
    timestamp = time.mktime(tuple)
    return int(timestamp)

def getActiveBinary(par):    
    arr = []
    for paridade in par['turbo']:
        if par['turbo'][paridade]['open'] == True: 
            arr.append(str(paridade))        
    return arr

def send(msg, chat_id, token):
	bot = telegram.Bot(token=token)
	bot.sendMessage(chat_id=chat_id, text=msg)

def Payout(par,tipo,timeframe):
    if(tipo=='turbo'):
        a = API.get_all_profit()
        return int(100*a[par]['turbo'])
    elif tipo == 'digital':
        API.subscribe_strike_list(par,timeframe)
        while True:
            d =API.get_digital_current_profit(par,timeframe)
            if d!= False:
                d = int (d)
                break
            time.sleep(1)
        API.subscribe_strike_list(par,timeframe)
        return d

def checkMsgSent(candleId):
    for i in range(len(signList)):
        if(signList[i] == candleId):
            return True
    return False

def getActualSeconds():
    current_time = time.ctime()
    return str(current_time[17:19])

#####################################################
############### FUNÇOES PRINCIPAIS ##################
#####################################################
    # ARRAY CANDLES EXAMPLES
    # SixthMirrorBreak
        # [i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5]
        # length: 11
    # SeventhhMirrorBreak
        # [i6,i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5,i6]
        # length: 13
    # EighthMirrorBreak
        # [i7,i6,i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5,i6,i7]
        # length: 15

def hasSixthMirrorBreak(par,tm,at):
    writeLog('Analysing '+str(par)+' for SixthBreak')
    x = getPastCandles(par,tm,tamFifth,at)
    ini = int(len(x)/2) 
    cont = 1
    while True:
        if(cont > dvFifth):
            return [True,getActualCandleColor(x,0),x[len(x)-1]['from'],x[len(x)-1]['id']]
        else:
            corAnt = getActualCandleColor(x,ini-cont)
            corPost = getActualCandleColor(x,ini+cont)
            if(corAnt != corPost):
                return [False,'','','']
            else:
                cont = cont + 1
# cont = 6
#   an             d              po
#   47 48 49 50 51 52 53 54 55 56 57
def hasSeventhhMirrorBreak(par,tm,at):
    writeLog('Analysing '+str(par)+' for SeventhBreak')
    x = getPastCandles(par,tm,tamSixth,at)
    ini = int(len(x)/2) 
    cont = 1
    while True:
        if(cont > dvSixth):
            return [True,getActualCandleColor(x,0),x[len(x)-1]['from'],x[len(x)-1]['id']]
        else:
            corAnt = getActualCandleColor(x,ini-cont)
            corPost = getActualCandleColor(x,ini+cont)
            if(corAnt != corPost):
                return [False,'','', '']
            else:
                cont = cont + 1

def hasEighthMirrorBreak(par,tm,at):
    writeLog('Analysing '+str(par)+' for EighthBreak')
    x = getPastCandles(par,tm,tamEighth,at)
    ini = int(len(x)/2) 
    cont = 1
    while True:
        if(cont > dvEighth):
            return [True,getActualCandleColor(x,0),x[len(x)-1]['from'],x[len(x)-1]['id']]
        else:
            corAnt = getActualCandleColor(x,ini-cont)
            corPost = getActualCandleColor(x,ini+cont)
            if(corAnt != corPost):
                return [False,'','','']
            else:
                cont = cont + 1



def start():
    while True:
        if(getActualSeconds() >= '20' and getActualSeconds() <= '50'):
            pares = API.get_all_open_time_v2() #Verificar isso  
            tm = 1
            if(int(tm) == int(M1[0])):
                tm = int(M1[1])
                tmp = 'M1'            
            if(int(tm) == int(M2[0])):
                tm = int(M2[1])
                tmp = 'M2'            
            if(int(tm) == int(M5[0])):
                tm = int(M5[1])
                tmp = 'M5'            
            if(int(tm) == int(M15[0])):
                tm = int(M15[1])
                tmp = 'M15'            
            if(int(tm) == int(M30[0])):   
                tm = int(M30[1])
                tmp = 'M30'            
            tipo = 'turbo'
            if pares is not None:
                par = pares[tipo]
                for k in range(len(par)):                       
                    payout = Payout(par[k].upper(),tipo,tm)  
                    if(payout != None):
                        if(payout >= 70):   
                            gerenciamento = ' Gerenciamento '
                            sixBreak = hasSixthMirrorBreak(par[k].upper(),tm,time.time())                                        
                            if(sixBreak[0]):
                                candleId = int(sixBreak[3])
                                if not (checkMsgSent(candleId)):
                                    signList.append(candleId)
                                    cor = 'vermelha' if(sixBreak[1] == 'Red') else 'verde' 
                                    op = 'Call 🔺' if (cor == 'vermelha') else 'Put 🔻'
                                    bola = '🟢' if(op == 'Call') else '🔴'
                                    tempo = timestamp_converter(sixBreak[2])
                                    header = '🕵🏻‍♀️ Sinal del Mago 🕵🏻‍♀️\n\n'
                                    body = '📊 Paridade: '+str(par[k].upper())+'\n⏰ Expiração: '+str(tmp)+'\n▶️ Entrada: '+str(getNextTime(tempo,1)[11:16])+' | '+str(op)+' '+str(bola) +'\n'                            
                                    body = body + '\nSe a vela atual ('+str(tempo[11:16])+') finalizar '+str(cor)+' realiza a entrada❗️'
                                    send(header + body,chat_id,my_token)
                            sevenBreak = hasSeventhhMirrorBreak(par[k].upper(),tm,time.time())                    
                            if(sevenBreak[0]):
                                candleId = int(sevenBreak[3])
                                if not (checkMsgSent(candleId)):
                                    signList.append(candleId)
                                    cor = 'vermelha' if(sevenBreak[1] == 'Red') else 'verde' 
                                    op = 'Call 🔺' if (cor == 'vermelha') else 'Put 🔻'
                                    bola = '🟢' if(op == 'Call') else '🔴'
                                    tempo = timestamp_converter(sevenBreak[2])
                                    header = '🕵🏻‍♀️ Sinal del Mago 🕵🏻‍♀️\n\n'
                                    body = '📊 Paridade: '+str(par[k].upper())+'\n⏰ Expiração: '+str(tmp)+'\n▶️ Entrada: '+str(getNextTime(tempo,1)[11:16])+' | '+str(op)+' '+str(bola) +'\n'                              
                                    body = body + '\nSe a vela atual ('+str(tempo[11:16])+') finalizar '+str(cor)+' realiza a entrada❗️'
                                    send(header + body,chat_id,my_token)
                            eigthBreak = hasEighthMirrorBreak(par[k].upper(),tm,time.time())                    
                            if(eigthBreak[0]):
                                candleId = int(eigthBreak[3])
                                if not (checkMsgSent(candleId)):
                                    signList.append(candleId)
                                    cor = 'vermelha' if(eigthBreak[1] == 'Red') else 'verde' 
                                    op = 'Call 🔺' if (cor == 'vermelha') else 'Put 🔻'
                                    bola = '🟢' if(op == 'Call') else '🔴'
                                    tempo = timestamp_converter(eigthBreak[2])
                                    header = '🕵🏻‍♀️ Sinal del Mago 🕵🏻‍♀️\n\n'
                                    body = '📊 Paridade: '+str(par[k].upper())+'\n⏰ Expiração: '+str(tmp)+'\n▶️ Entrada: '+str(getNextTime(tempo,1)[11:16])+' | '+str(op)+' '+str(bola) +'\n'                               
                                    body = body + '\nSe a vela atual ('+str(tempo[11:16])+') finalizar '+str(cor)+' realiza a entrada❗️'
                                    send(header + body,chat_id,my_token)

try:
    tmp = getCorrectHour()
    strTm = f'"{tmp}"'
    os.system('date -s '+str(tmp))
    start()      
except Exception as e:
    writeLog(e)
