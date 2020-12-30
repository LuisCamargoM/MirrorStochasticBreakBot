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
last_sign = []
contSignal = [0]
check = []

#TIMEFRAMES
M1 = [1,60]
M2 = [2,120]
M5 = [5,300]
M15 = [15,900]
M30 = [30,1800]


#####################################################
############### FUNÇOES AUXILIARES ##################
#####################################################
def getPastCandles(par,opTime,qtd,tm):                  
    vela = API.get_candles(par,opTime,qtd,tm)
    if vela is None:
        return 'None'
    else:    
        return vela

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

#####################################################
############### FUNÇOES PRINCIPAIS ##################
#####################################################
    # ARRAY CANDLES EXAMPLES
    # SixthMirrorBreak
        # [i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5]
        # length: 11
    # SeventhhMirrorBreak
        # [i6,i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5,i6]
        # length: 11
    # EighthMirrorBreak
        # [i7,i6,i5,i4,i3,i2,i1,D,i1,i2,i3,i4,i5,i6,i7]
        # length: 11

def hasSixthMirrorBreak(){
    print('Fifth Cyclo Mirror break')
}
def hasSeventhhMirrorBreak(){
    print('Seventh Cyclo Mirror break')
}
def hasEighthMirrorBreak(){
    print('Eighth Cyclo Mirror break')
}



while True:
    pares = API.get_all_open_time_v2() #Verificar isso  
    tm = 5
    tipo = 'turbo'
    if pares is not None:
        par = pares[tipo]
        for k in range(len(par)):                       
            payout = Payout(par[k].upper(),tipo,tm)  
            if(payout != None):
                if(payout >= 75):      
                    print('')    
                    #PEGAR AS PARIDADES ATIVAS -> done
                    #A CADA MINUTO VERIFICAR SE O SETUP SE CUMPRE
                    ### DEFINIR FUNCAO DO SETUP
                    # IF YES
                    #   #   Send Message 
        writeLog('')
        # time.sleep(60)


