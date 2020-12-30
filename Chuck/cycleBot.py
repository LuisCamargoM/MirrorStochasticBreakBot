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

#CYCLES
blue_cycle = [['Red','Red','Red'],['Green', 'Green', 'Green']]
pink_cycle = [['Red','Red','Green'],['Green', 'Green', 'Red']]

green_cycle = [['Red','Red','Green','Red','Green'],['Green','Green','Red','Green','Red']]
orange_cycle = [['Red','Red','Green','Red','Red'],['Green','Green','Red','Green','Green']]

#LIST
aux_list = [0,0]
aux_listgo = [0,0]
_list = []
_listgo = []

last_sign = []
contSignal = [0]
check = []

#SCENARIO
cycle_scenario = [[9,1], [8,2]]

#TIMEFRAMES
M1 = [1,60]
M2 = [2,120]
M5 = [5,300]
M15 = [15,900]
M30 = [30,1800]

#TIMEFRAMES_CATALOGATION - Minutes
CAT_M1 = 120 #2hrs
CAT_M2 = 240 #4hrs
CAT_M5 = 720 #12hrs
CAT_M15 = 2160 #36hrs
CAT_M30 = 4230 #72hrs


##########################################
############### FUNÇOES ##################
##########################################
def getPastCandles(par,opTime,qtd,tm):                  
    vela = API.get_candles(par,opTime,qtd,tm)
    if vela is None:
        return 'None'
    else:    
        return vela

def getActualCandleColor(x,pos):
    closeAnt = x[pos-1]['close']
    close = x[pos]['close']    
    # open = x[pos]['open']
    dif = close - closeAnt
    if (dif > 0):
        return 'Green' 
    if (dif < 0):
        return 'Red'
    if (dif == 0):
        return 'Doji' 

##########################################
######## X: ARRAY OF CANDLES #############
######## PosAtual: Posiçao atual #########
##########################################
def getNextTime(tm,min):
    t = datetime.strptime(str(tm),"%Y-%m-%d %H:%M:%S")
    delta = t + timedelta(minutes=min)
    return str(delta)

def getTimestamp(ts):
    element = datetime.strptime(str(ts),"%Y-%m-%d %H:%M:%S") 
    tuple = element.timetuple() 
    timestamp = time.mktime(tuple)
    return int(timestamp)

def getCycle(b):
    if (b == '🟣'): return 'rosa'
    if (b == '🔵'): return 'azul'
    if (b == '🟠'): return 'laranja'
    if (b == '🟢'): return 'verde'

def sendResults():
    try:
        tam = len(last_sign)
        header = '📊 Resultados dos Sinais 📊\n\n'        
        body = ''    
        for i in range(tam):
            #last_sign.append([contSignal[0],_list[lastTm][1],par,bola,p])                    
            signTime = last_sign[i][1]
            par = last_sign[i][2]
            cycle = getCycle(last_sign[i][3])
            nextTime = getNextTime(timestamp_converter(signTime),30)
            if(nextTime <= timestamp_converter(time.time())):
                y = getPastCandles(par,60,30,nextTime)
                j = 0
                while True:
                    if(j == len(y)):
                        body = body + '▶️ No. '+str(last_sign[i][0])+' | '+str(par)+' | Ciclo '+str(last_sign[i][3])+' - Loss ❌\n'
                        break
                    if(cycle == 'azul'):
                        check = checkIfHasBlueCycle(y,j)
                        if(check[0]):
                            body = body + '▶️ No. '+str(last_sign[i][0])+' | '+str(par)+' | Ciclo '+str(last_sign[i][3])+' - Win ✅\n'
                            break
                        else:
                            j = j + 1
                    if(cycle == 'rosa'):
                        check = checkIfHasPinkCycle(y,j)
                        if(check):
                            body = body + '▶️ No. '+str(last_sign[i][0])+' | '+str(par)+' | Ciclo '+str(last_sign[i][3])+' - Win ✅\n'
                            break
                        else:
                            j = j + 1
                    if(cycle == 'laranja'):
                        check = checkIfHasOrangeCycle(y,j)
                        if(check):
                            body = body + '▶️ No. '+str(last_sign[i][0])+' | '+str(par)+' | Ciclo '+str(last_sign[i][3])+' - Win ✅\n'
                            break
                        else:
                            j = j + 1
                    if(cycle == 'verde'):
                        check = checkIfHasGreenCycle(y,j)
                        if(check[0]):
                            body = body + '▶️ No. '+str(last_sign[i][0])+' | '+str(par)+' | Ciclo '+str(last_sign[i][3])+' - Win ✅\n'
                            break
                        else:
                            j = j + 1
            else:
                writeLog('Ainda nao passou 20 velas para conveferir o sinal\nHorario Sinal: '+timestamp_converter(signTime)+' - Horario Minimo'+str(nextTime))
        if(body != ''):
            message = header + body   
            send(message,chat_id,my_token)
    except Exception   as e:
        writeLog('SendResults Function \n'+str(e))

def getCheck(_id):
    for i in range(len(check)):
        if(int(_id) == int(check[i])):
            return False
    return True
def canSendSignal(txt,tam,par,tm,actualBola,actualP):  
    #last_sign.append([contSignal[0],_list[lastTm][1],par,bola,p])       
    #  if (b == '🟣'): return 'rosa'
    # if (b == '🔵'): return 'azul'
    # if (b == '🟠'): return 'laranja'
    # if (b == '🟢'): return 'verde'  
    for i in range(len(last_sign)):
        lastP = last_sign[i][4]
        if(actualP != lastP):
            lastBola = last_sign[i][3]
            foundP = lastP[1:]+lastBola
            if(foundP == actualP):
                writeLog('Ja aconteceu')
                writeLog(foundP+' - '+actualP)
                return False
    if(txt == 'laranja' or txt == 'verde'):
        #Verifica se ja foi enviado
        flvBool = True if ((len(last_sign) == 0) or (checkMsgSent(_listgo[tam][1],par) == False)) else False 
        signalTime = time.time()#int(_listgo[tam][1])
        x = getPastCandles(par,tm,5,signalTime)    
        colorIni = getActualCandleColor(x,0)
        #Verifica se na vela atual esta acontecendo o padrao ja
        sendingOG = True
        if(colorIni == getActualCandleColor(x,1) and colorIni != getActualCandleColor(x,2) and colorIni == getActualCandleColor(x,3)):
            sendingOG = False                            
        return flvBool and sendingOG
    if(txt == 'azul' or txt == 'rosa'):
        fbpBool = True if ((len(last_sign) == 0) or (checkMsgSent(_list[tam][1],par) == False)) else False
        signalTime = time.time() #int(_listgo[tam][1])
        x = getPastCandles(par,tm,3,signalTime) 
        sendingBP = True 
        if(getActualCandleColor(x,0) == getActualCandleColor(x,1)):
            sendingBP = False            
        return fbpBool and sendingBP
    
        
    

def changeCycle(txt):
    if(txt == 'rosa'):
        return 'azul'
    if(txt == 'azul'):
        return 'rosa'
    if(txt == 'verde'):
        return 'laranja'
    if(txt == 'laranja'):
        return 'verde'

def getPercentageBluenPink(tam):
    blue = 0
    pink = 0
    for i in range(tam):
        if(_list[i][0] == '🔵'):
            blue = blue + 1
        if(_list[i][0] == '🟣'):
            pink = pink + 1
    return [blue,pink]

def getPercentageGreennOrange(tam):
    green = 0
    orange = 0
    for i in range(tam):
        if(_listgo[i][0] == '🟢'):
            green = green + 1
        if(_listgo[i][0] == '🟠'):
            orange = orange + 1
    return [green,orange]

def checkMsgSent(signId,par):
    for i in range(len(last_sign)):
        if(last_sign[i][1] == signId and last_sign[i][2] == par):
            return True
    return False

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

def checkIfHasBlueCycle(x,posAtual):
    try:
        tam = len(x)
        contador = 0
        color = 'next'        
        if((posAtual + 3) >= tam):
            return ''
        for i in range(2):
            for j in range(3):
                # print(str(i) + ' - '+str(j+posAtual))
                #print(getActualCandleColor(x,j+posAtual)+' - '+timestamp_converter(x[j+posAtual]['from']))
                posvetor = j+posAtual        
                actualColor = getActualCandleColor(x,posvetor)
                cicloVela = blue_cycle[i][j]
                if(actualColor == cicloVela):  
                    #print(' - '+timestamp_converter(x[j+posAtual]['from']))
                    contador = contador + 1
                    color = blue_cycle[i][j]                
            if(contador == 3):
                # print('Blue Cycle Happens - '+timestamp_converter(x[posAtual]['from']))
                return [True,color]
            else:
                contador = 0
        if(contador < 3):
            return [False,color]                
    except Exception   as e:
        writeLog('Blue Cycle Function \n'+e)

def checkIfHasPinkCycle(x,posAtual):
    try:     
        tam = len(x)
        contador = 0        
        if((posAtual + 3) >= tam):
            return
        for i in range(2):
            for j in range(3):
                posvetor = j+posAtual                
                actualColor = getActualCandleColor(x,posvetor)
                cicloVela = pink_cycle[i][j]
                if(actualColor == cicloVela):  
                    contador = contador + 1                    
            if(contador == 3):                
                return True
            else:
                contador = 0
        if(contador < 3):            
            return False
    except Exception   as e:
        writeLog('Pink Cycle Function \n'+e)

def checkIfHasGreenCycle(x,posAtual):
    try:
        #print('Green Cycle Happens - '+timestamp_converter(x[posAtual]['from']))
        tam = len(x)
        contador = 0  
        color = 'next'      
        if((posAtual + 5) >= tam):
            return ''
        for i in range(2):
            for j in range(5):                
                posvetor = j+posAtual        
                actualColor = getActualCandleColor(x,posvetor)
                cicloVela = green_cycle[i][j]
                # print('Green Cycle Happens - '+timestamp_converter(x[posvetor]['from']))
                if(actualColor == cicloVela):  
                    contador = contador + 1
                    color = green_cycle[i][j]             
            if(contador == 5):
                #print('Green Cycle Happens - '+timestamp_converter(x[posAtual]['from']))
                return [True,color]
            else:
                contador = 0
        if(contador < 5):
            # print('checkIfHasGreenCycle')
            return [False,color]
    except Exception   as e:
        writeLog('Green Cycle Function \n'+e)   

def checkIfHasOrangeCycle(x,posAtual):
    try:
        #print('Orange Cycle Happens - '+timestamp_converter(x[posAtual]['from']))
        tam = len(x)
        contador = 0        
        if((posAtual + 5) >= tam):
            return ''
        for i in range(2):
            for j in range(5):
                posvetor = j+posAtual        
                actualColor = getActualCandleColor(x,posvetor)
                cicloVela = orange_cycle[i][j]                
                if(actualColor == cicloVela):  
                    contador = contador + 1                    
            if(contador == 5):
                #print('Orange Cycle Happens - '+timestamp_converter(x[posAtual]['from']))
                return True
            else:
                contador = 0
        if(contador < 5):
            # print('checkIfHasGreenCycle')
            return False
    except Exception as e:
        writeLog('Orange Cycle Function \n'+e)     

def printFullCycle():
    p = ''
    for i in (range((len(_list)))):
        p = p + _list[i][0]
    return p

def printFullCyclego():
    p = ''
    for i in (range((len(_listgo)))):
        p = p + _listgo[i][0]
    return p

def printSequence():
    p = ''
    tam = len(_list) - 1
    i = tam - 10
    while True:
        if(i == tam):
            break
        else:
            p = _list[tam][0] + p
            tam = tam - 1
    return p

def printSequencego():
    p = ''
    tam = len(_listgo) - 1
    i = tam - 10
    while True:
        if(i == tam):
            break
        else:
            p = _listgo[tam][0] + p
            tam = tam - 1
    return p

def startAnalysisBluenPink(tm,par):
    writeLog('Starting analysing Blue-Pink active pairs em: '+par)
    qtd = 0
    if(int(tm) == int(M1[0])):
        tm = int(M1[1])
        tmp = 'M1'
        qtd = CAT_M1
    if(int(tm) == int(M2[0])):
        tm = int(M2[1])
        tmp = 'M2'
        qtd = CAT_M2
    if(int(tm) == int(M5[0])):
        tm = int(M5[1])
        tmp = 'M5'
        qtd = CAT_M5
    if(int(tm) == int(M15[0])):
        tm = int(M15[1])
        tmp = 'M15'
        qtd = CAT_M15
    if(int(tm) == int(M30[0])):   
        tm = int(M30[1])
        tmp = 'M30'
        qtd = CAT_M30
    x = getPastCandles(par,tm,qtd,time.time())    
    i = 0
    while True:
        # print(timestamp_converter(x[i]['from']))
        if( i + 2 >= (len(x))):            
            break
        blueCycle = checkIfHasBlueCycle(x,i)
        pinkCycle = checkIfHasPinkCycle(x,i)          
        if(blueCycle == '' or pinkCycle == ''):      
            break
        if(pinkCycle):
            _list.append(['🟣',x[i+2]['from']])
            i = i + 1        
        else:            
            if(blueCycle[0]):
                _list.append(['🔵',x[i+2]['from']])
                cor = blueCycle[1] 
                if(i + 3 >= len(x)-1):
                    break
                i = i + 3
                if(cor != 'next'):
                    while True:
                        actualColor = getActualCandleColor(x,i)
                        if(i + 1 >= len(x)-1):
                            break                        
                        if(actualColor != cor):
                            break
                            #print('--- Quebra: '+' - '+ timestamp_converter(x[i]['from']))
                        else:
                            i = i + 1
            else:
                i = i + 1
    printFullCycle()
    if(len(_list) < 10):
        writeLog('Existem menos de 10 ciclos')
    else:        
        tam = len(_list) - 1
        j = tam - 10
        blue = 0
        pink = 0
        while True:
            # print(_list[j][0])
            if(tam == j):
                break
            else:
                if(_list[tam][0] == '🔵'):                        
                    blue = blue + 1    
                    actualBlue = aux_list[0]           
                    aux_list[0] = actualBlue+1
                else:
                    if(_list[tam][0] == '🟣'):                        
                        pink = pink + 1
                        actualPink = aux_list[1]
                        aux_list[1] = actualPink+1
                tam = tam - 1
        actualBlue = 0
        actualPink = 0
        header = '🔮 Sinal do Mago 🔮 \n\n'      
        body = '💰 Moeda: '+str(par)+'\n⏰ TimeFrame: '+str(tmp)+'\n'              
        p = printSequence()
        lastTm = len(_list) - 1
        [bl,pi] = getPercentageBluenPink(lastTm - 10)
        total = bl + pi    
        if (total == 0):
            # writeLog(aux_list)
            # writeLog(_list)
            # writeLog('Total == 0')
            writeLog('So existem 10 velas')
            total = 1        
        bluePl = round((bl/total)*100,0)
        pinkPl = round((pi/total)*100,0)
        dif = abs(bluePl - pinkPl)    
        equi = True if(dif <= 15) else False 
        #resposta = 'desequilibrio'
        if(equi):
            resposta = 'equilibrio' 
            if(pink == 8 and blue == 2):
                if(p[0:1] != '🔵'):
                    # placar = '📊 Placar: 🔵'+str(int(round((bl/total)*100,0)))+'%  x '+ '🟣'+str(int(round(((total-bl)/total)*100,0)))+ '%'
                    placar = '📊 Placar: 🔵'+str(bl)+' x '+ '🟣'+str(pi)+ ''                    
                    body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'                
                    op = 'azul' #changeCycle('azul') if (dif > 15) else 'azul'
                    # bola = '🔵' if op == 'azul' else '🟣'                
                    # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                 
                    bola = '🔵'#'🟠' if op == 'laranja' else '🟢'
                    message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                    body = body + message
                    writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                    if(canSendSignal('azul',lastTm,par,tm,op,p)):
                        send(header+body,chat_id,my_token)                    
                        contSignal[0] = contSignal[0] + 1
                        last_sign.append([contSignal[0], _list[lastTm][1],par,bola,p])                    
                        writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                    else:
                        writeLog('Ja foi enviado 1')
            else:
                if(pink == 2 and blue == 8):
                    if(p[0:1] != '🟣'):                                        
                        placar = '📊 Placar: 🔵'+str(bl)+' x '+ '🟣'+str(pi)+ ''                        
                        body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'   
                        op = 'rosa' #changeCycle('rosa') if (dif > 15) else 'rosa'
                        # bola = '🔵' if op == 'azul' else '🟣'
                        # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                                                             
                        bola = '🟣'#'🟠' if op == 'laranja' else '🟢'
                        message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                        body = body + message
                        writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                        if(canSendSignal('rosa',lastTm,par,tm,op,p)):
                            send(header+body,chat_id,my_token)
                            contSignal[0] = contSignal[0] + 1
                            last_sign.append([contSignal[0], _list[lastTm][1],par,bola,p])
                            writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                        else:
                            writeLog('Ja foi enviado 2')
                else:
                    if(pink == 9 and blue == 1):
                        if(p[0:1] != '🔵'):                                                    
                            placar = '📊 Placar: 🔵'+str(bl)+' x '+ '🟣'+str(pi)+ ''                            
                            body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'
                            op = 'azul' #changeCycle('azul') if (dif > 15) else 'azul'
                            # bola = '🔵' if op == 'azul' else '🟣'
                            # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                                                         
                            bola = '🔵'#'🟠' if op == 'laranja' else '🟢'
                            message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                            body = body + message      
                            writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                            if(canSendSignal('azul',lastTm,par,tm,op,p)):
                                send(header+body,chat_id,my_token)
                                contSignal[0] = contSignal[0] + 1
                                last_sign.append([contSignal[0], _list[lastTm][1],par,bola,p]) 
                                writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                            else:
                                writeLog('Ja foi enviado 3')                   
                    else:
                        if(pink == 1 and blue == 9):
                            if(p[0:1] != '🟣'):                                                            
                                placar = '📊 Placar: 🔵'+str(bl)+' x '+ '🟣'+str(pi)+ ''                                
                                body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'
                                op = 'rosa' #changeCycle('rosa') if (dif > 15) else 'rosa'
                                # bola = '🔵' if op == 'azul' else '🟣'
                                # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                                                            
                                bola = '🟣'#'🟠' if op == 'laranja' else '🟢'
                                message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                                body = body + message
                                writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                                if(canSendSignal('rosa',lastTm,par,tm,op,p)):
                                    send(header+body,chat_id,my_token)
                                    contSignal[0] = contSignal[0] + 1
                                    last_sign.append([contSignal[0], _list[lastTm][1],par,bola,p])
                                    writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                                else:
                                    writeLog('Ja foi enviado 4')                           
                        else:
                            # print(printFullCycle())                                                  
                            _list.clear()     

def startAnalysisGreebnOrange(tm,par):
    writeLog('Starting analysing Green-Orange active pairs em: '+par)
    qtd = 0
    if(int(tm) == int(M1[0])):
        tm = int(M1[1])
        tmp = 'M1'
        qtd = CAT_M1
    if(int(tm) == int(M2[0])):
        tm = int(M2[1])
        tmp = 'M2'
        qtd = CAT_M2
    if(int(tm) == int(M5[0])):
        tm = int(M5[1])
        tmp = 'M5'
        qtd = CAT_M5
    if(int(tm) == int(M15[0])):
        tm = int(M15[1])
        tmp = 'M15'
        qtd = CAT_M15
    if(int(tm) == int(M30[0])):   
        tm = int(M30[1])
        tmp = 'M30'
        qtd = CAT_M30
    x = getPastCandles(par,tm,qtd,time.time())    
    i = 0
    while True:
        if (i + 4 >= (len(x))):
            break
        greenCycle = checkIfHasGreenCycle(x,i)
        orangeCycle = checkIfHasOrangeCycle(x,i)
        if (greenCycle == '' or orangeCycle == ''):
            break
        if(orangeCycle):
            _listgo.append(['🟠',x[i+4]['from']])             
            i = i + 1
        else:
            if(greenCycle[0]):
                _listgo.append(['🟢',x[i+4]['from']]) 
                cor = greenCycle[1]
                if(i + 4 >= len(x)):
                    break
                i = i + 5
                if(cor != 'next'):
                    while True:
                        actualColor = getActualCandleColor(x,i)
                        if(i+1 >= len(x)):
                            break
                        if(actualColor == cor):
                            break
                        else:
                            i = i + 1
            else:
                i = i + 1
    printFullCyclego()
    if(len(_listgo) < 10):
        writeLog('Existem menos de 10 ciclos')
    else:
        tam = len(_listgo) - 1
        j = tam - 10
        green = 0
        orange = 0
        while True:    
            if(tam == j):
                break
            else: 
                if(_listgo[tam][0] == '🟢'):                       
                    green = green + 1        
                    actualGreen = aux_listgo[0]       
                    aux_listgo[0] = actualGreen+1
                else:
                    if(_listgo[tam][0] == '🟠'):                        
                        orange = orange + 1
                        actualOrange = aux_listgo[1]
                        aux_listgo[1] = actualOrange+1
                tam = tam - 1  
        actualOrange = 0
        actualGreen = 0
        header = '🔮 Sinal do Mago 🔮 \n\n'      
        body = '💰 Moeda: '+str(par)+'\n⏰ TimeFrame: '+str(tmp)+'\n'              
        p = printSequencego()
        lastTm = len(_listgo) - 1
        [gr,org] = getPercentageGreennOrange(lastTm - 10)
        total = gr + org
        if (total == 0):
            # writeLog(aux_listgo)
            # writeLog(_listgo)
            # writeLog('Total == 0')
            writeLog('So existem 10 velas')
            total = 1

        greenPl = round((gr/total)*100,0)
        orangePl = round((org/total)*100,0)
        dif = abs(greenPl - orangePl)
        equi = True if(dif <= 15) else False 
        #resposta = 'desequilibrio'
        if(equi):
            resposta = 'equilibrio'                
            if(green == 8 and orange == 2):
                if(p[0:1] != '🟠'):                    
                    placar = '📊 Placar: 🟢'+str(gr)+' x '+ '🟠'+str(org)+ ''
                    body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'
                    op = 'laranja' #changeCycle('laranja') if (dif > 15) else 'laranja'
                    bola = '🟠'#'🟠' if op == 'laranja' else '🟢'
                    message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                    body = body + message
                    writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                    if(canSendSignal('laranja',lastTm,par,tm,op,p)):
                        send(header+body,chat_id,my_token)
                        contSignal[0] = contSignal[0] + 1
                        last_sign.append([contSignal[0], _listgo[lastTm][1],par,bola,p])
                        writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                    else:
                        writeLog('Ja foi enviado 1')
            else:
                if(green == 2 and orange == 8):
                    if(p[0:1] != '🟢'):                                        
                        placar = '📊 Placar: 🟢'+str(gr)+' x '+ '🟠'+str(org)+ ''                        
                        body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n' 
                        op = 'verde'#changeCycle('verde') if (dif > 15) else 'verde' 
                        # bola = '🟠' if op == 'laranja' else '🟢'          
                        # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                 
                        bola = '🟢'#'🟠' if op == 'laranja' else '🟢'
                        message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                        body = body + message
                        writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                        if(canSendSignal('verde',lastTm,par,tm,op,p)):
                            send(header+body,chat_id,my_token)
                            contSignal[0] = contSignal[0] + 1
                            last_sign.append([contSignal[0], _listgo[lastTm][1],par,bola,p])
                            writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                        else:
                            writeLog('Ja foi enviado 2')
                else:
                    if(green == 9 and orange == 1):
                        if(p[0:1] != '🟠'):                                                    
                            placar = '📊 Placar: 🟢'+str(gr)+' x '+ '🟠'+str(org)+ ''                            
                            body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'
                            op = 'laranja'#changeCycle('laranja') if (dif > 15) else 'laranja'       
                            # bola = '🟠' if op == 'laranja' else '🟢'    
                            # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                  
                            bola = '🟠'#'🟠' if op == 'laranja' else '🟢'
                            message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                            body = body + message      
                            writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                            if(canSendSignal('laranja',lastTm,par,tm,op,p)):
                                #Acicionar a lista e verificar se ja houve alguma paridade Verificar 
                                send(header+body,chat_id,my_token)
                                contSignal[0] = contSignal[0] + 1
                                last_sign.append([contSignal[0], _listgo[lastTm][1],par,bola,p])
                                writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola)) 
                            else:
                                writeLog('Ja foi enviado 3')                   
                    else:
                        if(green == 1 and orange == 9):
                            if(p[0:1] != '🟢'):                            
                                #placar = '📊 Placar: 🟢'+str(int(round((gr/total)*100,0)))+'%  x '+ '🟠'+str(int(round(((total-gr)/total)*100,0)))+ '%'
                                placar = '📊 Placar: 🟢'+str(gr)+' x '+ '🟠'+str(org)+ ''                                
                                body = body +placar + '\n♻️ Ciclo: '+str(p) + '\n\n'
                                op = 'verde'#changeCycle('verde') if (dif > 15) else 'verde' 
                                # bola = '🟠' if op == 'laranja' else '🟢'
                                # message = 'Entrada para o '+str(resposta)+' - ciclo '+str(op)                                  
                                bola = '🟢'#'🟠' if op == 'laranja' else '🟢'
                                message = 'Entrada para o ciclo '+str(bola)#+str(resposta)+' - ciclo '+str(op)                                          
                                body = body + message
                                writeLog('Enviar '+str(resposta)+' - ciclo '+str(op))
                                if(canSendSignal('verde',lastTm,par,tm,op,p)):
                                    contSignal[0] = contSignal[0] + 1
                                    send(header+body,chat_id,my_token)
                                    last_sign.append([contSignal[0], _listgo[lastTm][1],par,bola,p])
                                    writeLog('***********'+str(timestamp_converter(time.time()))+','+str(time.time())+','+str(bola))
                                else:
                                    writeLog('Ja foi enviado 4')                           
                        else:
                            # print(printFullCycle())                                                  
                            _listgo.clear()

while True:
    pares = API.get_all_open_time_v2() #Verificar isso  
    tm = 5
    tipo = 'turbo'
    if pares is not None:
        par = pares[tipo]
        for k in range(len(par)):                       
            payout = Payout(par[k].upper(),tipo,tm)  
            if(payout != None):
                if(payout >= 70):      
                    startAnalysisBluenPink(tm,par[k].upper())
                    startAnalysisGreebnOrange(tm,par[k].upper())
                    # if(timestamp_converter(time.time())[15:16] == '4' or timestamp_converter(time.time())[15:16] == '9' and timestamp_converter(time.time())[17:19] == '00'):
                    #     sendResults()
        writeLog('')
        # time.sleep(60)


