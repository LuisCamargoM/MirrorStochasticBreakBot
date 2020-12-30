import logging
# import bot_conf as config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters,CallbackQueryHandler
from telegram import InlineKeyboardMarkup,InlineKeyboardButton
import csv
from iqoptionapi.stable_api import IQ_Option
import telegram 
from datetime import datetime,timedelta
import chuckTelegramConfig as tel
from time import strftime
import time
from dateutil import tz
import os
import signal


API = IQ_Option('luis.e.c.mendoza@gmail.com','Luis_@2020!')
API.connect()
API.change_balance('PRACTICE')

while True:
    if API.check_connect() == False:        
        #print('Erro ao se conectar!')    
        API.connect()    
    else:
        #print('Conectado com sucesso! '+str(os.getpid()))
        break

HORARIO_FINAL = ' 23:59'
HORARIO_INICIAL = ' 00:00'

# ARRAY_ACTIVES = ['AUDJPY','AUDUSD','AUDCAD','EURAUD','EURGBP','EURJPY','EURUSD','GBPCAD','GBPJPY', 'GBPUSD', 'USDCAD','USDJPY','USDCHF']
# ARRAY_OTC = ['EURUSD-OTC','EURGBP-OTC','USDCHF-OTC','EURJPY-OTC','GBPUSD-OTC','NZDUSD-OTC','AUDCAD-OTC','USDJPY-OTC','GBPJPY-OTC']

MIN_PROFIT = 0.0
M30 = 30
M1 = 60
M5 = 300
MINIMUM_M1 = 30
MININUM_M5 = 30
MINIMUM_30s = 30

def getValActual(w,g,l,d,banca,payout,stake):    
    s = (stake/100) * banca
    p = (payout/100)
    win = (p * s) * w    
    gale = ((2*s)*p - (s))*g   
    doji = l*s*d
    loss = l*(s+(2*s)) 
    return banca + (win + gale - (loss+doji))

def getValActualSG(w,l,banca,payout,stake):    
    s = (stake/100) * banca
    p = (payout/100)
    win = (p * s) * w      
    loss = l*(s*p) 
    return banca + (win - (loss))

def getActiveDigital(par):    
    arr = []
    for paridade in par['digital']:
        if par['digital'][paridade]['open'] == True:
            arr.append(paridade)            
    return arr

def getActualCandleColor(x,pos):
    close = x[pos]['close']    
    open = x[pos]['open']
    if (close-open) > 0:
        return 'Green' 
    if (close-open) < 0:
        return 'Red'
    return 'Doji'

def standarIniDate(data):
    string = data + HORARIO_INICIAL+':00' #"2020-09-18 00:00:00"
    return time.mktime(datetime.strptime(string,"%Y-%m-%d %H:%M:%S").timetuple()) 

def standarFinalDate(data):
    string = data + HORARIO_FINAL+':00' #"2020-09-18 00:00:00"
    return time.mktime(datetime.strptime(string,"%Y-%m-%d %H:%M:%S").timetuple())

def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))
    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

def getMinuteFromTimestamp(data):
    return timestamp_converter(data)[14:16]

""" SETUP GG """
def checkGG(arr,win,g1,loss):
    w = win
    g = g1
    l = loss
    firstCandle = getActualCandleColor(arr,1)
    fourthCandle = getActualCandleColor(arr,4)
    message = ''
    if(firstCandle == 'Doji' and fourthCandle == 'Doji'):
        message = message + timestamp_converter(arr[1]['from']) + ' ➕\n'
        return [w,g,l,'-',message]     
    if(firstCandle == 'Red' and fourthCandle == 'Red'):
        l = l + 1        
        message = message + timestamp_converter(arr[1]['from']) + ' ❌\n'
        return [w,g,l,'x',message]
    if(firstCandle == 'Red' and fourthCandle == 'Green'):  
        w = w + 1
        message = message + timestamp_converter(arr[1]['from']) + ' 🐔\n'
        return [w,g,l,'-',message]
    if(firstCandle == 'Green'):
        w = w + 1
        message = message + timestamp_converter(arr[1]['from']) + ' ✅\n'
        return [w,g,l,'-',message]
    return [w,g,l,'-',message]

def verifyGG(par,qtd,actualTime):    
    confirm = True
    win = 0
    g1 = 0
    loss = 0
    cont = 0 
    entra = True
    lastLoss = ''
    message = ''
    while confirm:
        x = API.get_candles(par,60,6,actualTime)   
        #print(timestamp_converter(x[5]['from'])[11:])
        result = checkGG(x,win,g1,loss)
        win = result[0]
        g1 = result[1]
        loss = result[2]
        message = result[4] + message 
        if(cont == qtd):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False      
        if(result[3] != '-' and entra == True):
            lastLoss = timestamp_converter(x[1]['from'])[11:]
            #print('Loss - '+timestamp_converter(x[1]['from']))
            entra = False
        cont = cont + 1
        actualTime = x[0]['from']

    #p = win + g1 + loss    
    return [win, g1, loss,lastLoss, message]

    # header = '******** Setup GG ********\n\n📊 '+par
    # body = '\n✅Win: '+ str(float(wn))+ '\n❌Loss: '+str(loss)+'\n\n Ultimo Loss: '+str(lastLoss)+'\n'
    
    # time.sleep(3)
    # update.message.reply_text(header+body)

def getTimeCandleGG(par):
    lastCandles = API.get_candles(par,60,6,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 4):
            return lastCandles[i]['from']

""" SETUP M3 """
def checkM3(arr,win,g1,loss):
    w = win
    g = g1
    l = loss
    message = ''
    for i in reversed(range(len(arr))):
        candle = getActualCandleColor(arr,i)
        if(candle == 'Doji'):
            # message = message + timestamp_converter(arr[i]['from']) + ' ➕\n'
            return [w,l,'-','']
            
    firstCandle = getActualCandleColor(arr,1)
    secondCanle = getActualCandleColor(arr,2)
    thirdCandle = getActualCandleColor(arr,3)
    fourthCandle = getActualCandleColor(arr,4)
    fifthCandle = getActualCandleColor(arr,5)
    sixthCandle = getActualCandleColor(arr,6)

    
    if(firstCandle != secondCanle):
        if(thirdCandle == fourthCandle and fourthCandle == fifthCandle):
            if(sixthCandle == fifthCandle):
                w = w + 1
                message = message + timestamp_converter(arr[1]['from']) + ' ✅\n'
                #print('Win - '+timestamp_converter(arr[1]['from'])+' -> '+str(timestamp_converter(arr[0]['from'])+' -> '+str(timestamp_converter(arr[5]['from']))))
                return [w,l,'-',message]
            else:
                l = l + 1 
                message = message + timestamp_converter(arr[1]['from']) + ' ❌\n'
                #print('Loss - '+timestamp_converter(arr[1]['from'])+' -> '+str(timestamp_converter(arr[0]['from'])+' -> '+str(timestamp_converter(arr[5]['from']))))
                return [w,l,'x',message]
               
    return [w,l,'-',message]

def verifyM3(par,qtd,actualTime):    
    confirm = True
    win = 0
    g1 = 0
    loss = 0
    cont = 0 
    entra = True
    lastLoss = ''
    message = ''
    while confirm:
        x = API.get_candles(par,60,7,actualTime)   
        #print(timestamp_converter(x[5]['from'])[11:])
        result = checkM3(x,win,g1,loss)
        win = result[0]
        loss = result[1]         
        message = result[3] + message 
        if(cont == qtd):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False      
        if(result[3] != '-' and entra == True):
            lastLoss = timestamp_converter(x[1]['from'])[11:]
            #print('Loss - '+timestamp_converter(x[1]['from']))
            entra = False
        cont = cont + 1
        actualTime = x[1]['from']

    #p = win + g1 + loss
    return [win,loss, lastLoss, message]

    # header = '******** Setup M3 ********\n\n📊 '+par
    # body = '\n✅Win: '+ str(float(wn))+ '\n❌Loss: '+str(loss)+'\n\n Ultimo Loss: '+str(lastLoss)+'\n'
    
    # time.sleep(3)
    # update.message.reply_text(header+body)

def getTimeCandleM3(par):
    lastCandles = API.get_candles(par,60,7,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 0):
            #print(timestamp_converter(lastCandles[0]['from']))
            return lastCandles[i]['from']

""" SETUP Twins """
def checkEngolfo(arr,first,second):
    firstColor = getActualCandleColor(arr,first)
    if(firstColor == 'Green'):
        return arr[second]['close'] <= arr[first]['open']
    if(firstColor == 'Red'):
        return arr[second]['close'] >= arr[first]['open']

def checkTwins(arr,win,loss):
    w = win
    l = loss
    message = ''
    for i in range(6):
        candle = getActualCandleColor(arr,i)
        if(candle == 'Doji'):
            return [w,l,'']
    firstCandle = getActualCandleColor(arr,0)
    secondCanle = getActualCandleColor(arr,1)
    thirdCandle = getActualCandleColor(arr,2)
    fourthCandle = getActualCandleColor(arr,3)
    fifthCandle = getActualCandleColor(arr,4)

    engolfo = checkEngolfo(arr,1,2)
    if(firstCandle == secondCanle):
        if(thirdCandle != secondCanle):
            if(engolfo):                
                if(thirdCandle == fourthCandle):                
                    if(fourthCandle == fifthCandle):
                        w = w + 1
                        message = message + timestamp_converter(arr[1]['from']) + ' ✅\n'
                        #print('Win - '+timestamp_converter(arr[1]['from']))
                        return [w,l,message]
                    else:
                        l = l + 1 
                        message = message + timestamp_converter(arr[1]['from']) + ' ❌\n'
                        #print('Loss - '+timestamp_converter(arr[1]['from']))
                        return [w,l,message]
               
    return [w,l,message]

def verifyTwins(par,qtd,actualTime):    
    confirm = True
    win = 0
    loss = 0
    cont = 0 
    entra = True
    lastLoss = ''
    message = ''
    
    while confirm:
        x = API.get_candles(par,60,6,actualTime)   
        #print(timestamp_converter(x[5]['from'])[11:])
        result = checkTwins(x,win,loss)
        win = result[0]  
        loss = result[1]
        message = result[2] + message 
        if(cont == qtd):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False      
        if(result[2] != '-' and entra == True):
            lastLoss = timestamp_converter(x[1]['from'])[11:]
            #print('Loss - '+timestamp_converter(x[1]['from']))
            entra = False
        cont = cont + 1
        actualTime = x[0]['from']

    #p = win + g1 + loss
    return [win, loss,lastLoss,message]
    
def getTimeCandleTwins(par):
    lastCandles = API.get_candles(par,60,6,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 4):
            #print(timestamp_converter(lastCandles[i]['from']))
            return lastCandles[i]['from']


def getGG(update,context):
    #update.message.reply_text('Getting GG Setup Catalog.....')                  
    resp = update['message']['text'].split(' ')
    paridade = str(resp[1].upper())
    qtdVelas = int(resp[2])                    
    actualTimeGG = int(getTimeCandleGG(paridade))
    [wn, g, loss,lastLoss,message] =  verifyGG(paridade,qtdVelas,actualTimeGG)
    total = wn + loss        
    header = '<<<< BACKTEST GG - '+str(paridade)+' >>>>\n\n'
    banca = 1000        
    payout = 80
    stake = 5
    resultado = round(getValActual(wn,g,loss,0,banca,payout,stake),2)
    simulation = 'Positivo' if resultado > banca else 'Empatou' if resultado == banca else 'Negativo'
    body = '\n\nSimulaçao de valores\nBanca: '+str(banca)+'\nStake: '+str(stake)+'%\nPayout: '+str(payout)+'%\n'+'Banca Final:'+str(resultado)
    body = header + message + body#'📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
    update.message.reply_text(body)                

def getM3(update,context):
    resp = update['message']['text'].split(' ')
    paridade = str(resp[1].upper())
    qtdVelas = int(resp[2])                    
    actualTimeM3 = int(getTimeCandleM3(paridade))
    [wn, loss,lastLoss,message] =  verifyM3(paridade,qtdVelas,actualTimeM3)
    total = wn + loss        
    header = '<<<< BACKTEST M3 - '+str(paridade)+' >>>>\n\n'
    banca = 1000        
    payout = 80
    stake = 5
    resultado = round(getValActualSG(wn,loss,banca,payout,stake),2)
    simulation = 'Positivo' if resultado > banca else 'Empatou' if resultado == banca else 'Negativo'
    body = '\n\nSimulaçao de valores\nBanca: '+str(banca)+'\nStake: '+str(stake)+'%\nPayout: '+str(payout)+'%\n'+'Banca Final:'+str(resultado)
    body = header + message + body#'📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
    update.message.reply_text(body)  


def verifySequenceM1(paridade,actualTime):    
    confirm = True
    countRed = 0
    countGreen = 0
    zika = 0
    actualTime = time.time()

    cont = 0 
    entra = True
    
    
    while confirm:        
        x = API.get_candles(paridade,M1,3,actualTime)       
        firstCandle = getActualCandleColor(x,0)
        secondCandle = getActualCandleColor(x,1)
        thirdCandle = getActualCandleColor(x,2)
        if(firstCandle != secondCandle):
            if(secondCandle != thirdCandle):
                zika = zika + 1
                print('Par: '+paridade+ ' - '+timestamp_converter(x[1]['from']))
            else:
                if(firstCandle == 'Green' and secondCandle == 'Red' and thirdCandle == 'Red'):                
                    countRed = countRed + 1
                if(firstCandle == 'Red' and secondCandle == 'Green' and thirdCandle == 'Green'):
                    countGreen = countGreen + 1
                    

        if(cont == MINIMUM_M1):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False              
        cont = cont + 1
        actualTime = x[1]['from']
        #print(timestamp_converter(actualTime))

    #p = win + g1 + loss
    return [countGreen, countRed,zika]

def getMayoritySequenceM1(update,context):
    update.message.reply_text('Getting Sequence Setup Catalog.....')   
    par = API.get_all_open() #Get all Open Actives 
    pares = []
    if par is not None:                
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):   
            paridade = a[t].upper() # Caps Lock
            actualTime = time.time()
            [countGreen, countRed, zika] = verifySequenceM1(paridade,actualTime)            
            total = countRed + countGreen
            if(total != 0):
                if(countRed == countGreen):
                    mayority = 'Balanced'
                    pares.append([paridade,mayority,total/total,zika])
                if(countRed > countGreen):
                    mayority = 'Red'
                    pares.append([paridade,mayority,countRed/total,zika])
                if(countRed < countGreen):
                    mayority = 'Green'
                    pares.append([paridade,mayority,countGreen/total,zika])
        tam = len(pares)
        body = '<<<< Setup Sequence M1 >>>>\n\n'
        if(tam <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tam):
                perc = round(float(pares[i][2]*100),2)                
                body = body + '📊'+ str(pares[i][0]) + ' - ' + str(pares[i][1])+ ' ( '+str(perc)+'% )'+ '\nZikas: '+str(pares[i][3])+'\n\n'
        update.message.reply_text(body)
                
def verifySequenceM5(paridade,actualTime):    
    confirm = True
    countRed = 0
    countGreen = 0
    zika = 0
    actualTime = time.time()

    entra = True
    
    
    while confirm:        
        x = API.get_candles(paridade,M5,3,actualTime)       
        firstCandle = getActualCandleColor(x,0)
        secondCandle = getActualCandleColor(x,1)
        thirdCandle = getActualCandleColor(x,2)
        if(firstCandle != secondCandle):
            if(secondCandle != thirdCandle):
                zika = zika + 1
                print('Par: '+paridade+ ' - '+timestamp_converter(x[1]['from']))
            else:
                if(firstCandle == 'Green' and secondCandle == 'Red' and thirdCandle == 'Red'):                
                    countRed = countRed + 1
                if(firstCandle == 'Red' and secondCandle == 'Green' and thirdCandle == 'Green'):
                    countGreen = countGreen + 1
                

        if(cont == MININUM_M5):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False              
        cont = cont + 1
        actualTime = x[1]['from']
        #print(timestamp_converter(actualTime))

    #p = win + g1 + loss
    return [countGreen, countRed, zika]

def getMayoritySequenceM5(update,context):
    update.message.reply_text('Getting Sequence Setup Catalog.....')   
    par = API.get_all_open() #Get all Open Actives 
    pares = []
    if par is not None:                
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):   
            paridade = a[t].upper() # Caps Lock
            actualTime = time.time()
            [countGreen, countRed, zika] = verifySequenceM5(paridade,actualTime)            
            total = countRed + countGreen
            if(total != 0):
                if(countRed == countGreen):
                    mayority = 'Balanced'
                    pares.append([paridade,mayority,total/total,zika])
                if(countRed > countGreen):
                    mayority = 'Red'
                    pares.append([paridade,mayority,countRed/total,zika])
                if(countRed < countGreen):
                    mayority = 'Green'
                    pares.append([paridade,mayority,countGreen/total,zika])
        tam = len(pares)
        body = '<<<< Setup Sequence M5 >>>>\n\n'
        if(tam <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tam):
                perc = round(float(pares[i][2]*100),2)                
                body = body + '📊'+ str(pares[i][0]) + ' - ' + str(pares[i][1])+ ' ( '+str(perc)+'% )'+ '\nZikas: '+str(pares[i][3])+'\n\n'
        update.message.reply_text(body)
                
def verifySequence30s(paridade,actualTime):    
    confirm = True
    countRed = 0
    countGreen = 0
    zika = 0
    actualTime = time.time()

    cont = 0 
    entra = True
    
    
    while confirm:        
        x = API.get_candles(paridade,M30,3,actualTime)       
        firstCandle = getActualCandleColor(x,0)
        secondCandle = getActualCandleColor(x,1)
        thirdCandle = getActualCandleColor(x,2)
        if(firstCandle != secondCandle):
            if(secondCandle != thirdCandle):
                zika = zika + 1
                print('Par: '+paridade+ ' - '+timestamp_converter(x[1]['from']))
            else:
                if(firstCandle == 'Green' and secondCandle == 'Red' and thirdCandle == 'Red'):                
                    countRed = countRed + 1
                if(firstCandle == 'Red' and secondCandle == 'Green' and thirdCandle == 'Green'):
                    countGreen = countGreen + 1
                

        if(cont == MINIMUM_30s):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False              
        cont = cont + 1
        actualTime = x[1]['from']
        #print(timestamp_converter(actualTime))

    #p = win + g1 + loss
    return [countGreen, countRed, zika]

def getMayoritySequence30s(update,context):
    update.message.reply_text('Getting Sequence Setup Catalog.....')   
    par = API.get_all_open() #Get all Open Actives 
    pares = []
    if par is not None:                
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):   
            paridade = a[t].upper() # Caps Lock
            actualTime = time.time()
            [countGreen, countRed, zika] = verifySequence30s(paridade,actualTime)            
            total = countRed + countGreen
            if(total != 0):
                if(countRed == countGreen):
                    mayority = 'Balanced'
                    pares.append([paridade,mayority,total/total,zika])
                if(countRed > countGreen):
                    mayority = 'Red'
                    pares.append([paridade,mayority,countRed/total,zika])
                if(countRed < countGreen):
                    mayority = 'Green'
                    pares.append([paridade,mayority,countGreen/total,zika])
        tam = len(pares)
        body = '<<<< Setup Sequence 30s >>>>\n\n'
        if(tam <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tam):
                perc = round(float(pares[i][2]*100),2)                
                body = body + '📊'+ str(pares[i][0]) + ' - ' + str(pares[i][1])+ ' ( '+str(perc)+'% )'+ '\nZikas: '+str(pares[i][3])+'\n\n'
        update.message.reply_text(body)
                
def getTwins(update,context):
    resp = update['message']['text'].split(' ')
    paridade = str(resp[1].upper())
    print(paridade)
    qtdVelas = int(resp[2])                    
    print(qtdVelas)
    actualTimeTwins = int(getTimeCandleTwins(paridade))
    [wn, loss,lastLoss,message] =  verifyTwins(paridade,qtdVelas,actualTimeTwins)        
    total = wn + loss        
    header = '<<<< BACKTEST TWINS - '+str(paridade)+' >>>>\n\n'
    banca = 1000        
    payout = 80
    stake = 5
    resultado = round(getValActualSG(wn,loss, banca,payout,stake),2)
    simulation = 'Positivo' if resultado > banca else 'Empatou' if resultado == banca else 'Negativo'
    body = '\n\nSimulaçao de valores\nBanca: '+str(banca)+'\nStake: '+str(stake)+'%\nPayout: '+str(payout)+'%\n'+'Banca Final:'+str(resultado)
    body = header + message + body#'📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
    update.message.reply_text(body)         

    # update.message.reply_text('Getting Twins Setup Catalog.....')
    # par = API.get_all_open() #Get all Open Actives 
    # pares = []            
    # if par is not None:                
    #     a = getActiveDigital(par) # Filter Digital Open Actives            
    #     for t in range(len(a)):   
    #         paridade = a[t].upper() # Caps Lock
    #         actualTimeTwins = int(getTimeCandleTwins(paridade))
    #         [wn, loss,lastLoss] =  verifyTwins(paridade,actualTimeTwins)
    #         total = wn + loss
    #         if(total != 0):
    #             assertividade = wn/total
    #             if(assertividade >= MIN_PROFIT):
    #                 pares.append([paridade,wn,loss,round(assertividade*100,2),lastLoss])
    #     tamPares = len(pares)
    #     body = '<<<< Setup Twins >>>>\n\n'
    #     if(tamPares <= 0):
    #         body = 'Nao aconteceu este padrao !!'
    #     else:
    #         for i in range(tamPares):
    #             body = body + '📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
    #     update.message.reply_text(body) 

def verifyCandle(x,actual,past):
    if(x[actual]['close'] == x[past]['close']):
        return 'Doji'
    if(x[actual]['close'] > x[past]['close']):
        return 'Green'
    if(x[actual]['close'] < x[past]['close']):
        return 'Red'

def getFirstTime(x,today,win,gale,loss):
        ini = []
        i = 0
        lost = ''
        tam = len(x)
        while True:
            temp = x[i]['from']
            tempo = timestamp_converter(int(temp))            
            if ( (tempo[14:16] == '58' and tempo[11:13] >= '00' and tempo[8:10] == today) or (tempo[11:13] == '23' and tempo[14:16] == '58' and tempo[8:10] != today)):                
                #if (tempo[14:16] == '58'): #and tempo[8:10] == today): #and tempo[8:10] == today):
                #return temp
                n = i
                while True: 
                    #print(n)
                    if( n+11 > tam):
                        break
                    cor = verifyCandle(x,n,n-1)
                    #print(' Hora : '+str(timestamp_converter(int(x[n]['from'])))+' | Color: '+str(cor))
                    if ( cor == 'Doji'):
                        n = n + 7
                        continue
                    else:
                        if (verifyCandle(x,n+9,n+8) == 'Doji'):
                            n = n + 7 
                            continue
                        else:
                            if (cor == verifyCandle(x,n+9,n+8)):                    
                                temp = x[n+9]['from']
                                tempo = timestamp_converter(int(temp))                                    
                                n = n + 7
                                print(' win!  '+tempo + ' | n :'+str(n))
                                win = win + 1
                            else:
                                if (cor == verifyCandle(x,n+10,n+9)):                        
                                    temp = x[n+10]['from']
                                    tempo = timestamp_converter(int(temp))                                        
                                    n = n + 7
                                    print(' Gale! '+tempo + ' | n :'+str(n))
                                    gale = gale + 1                                                                             
                                else:                                      
                                    temp = x[n+10]['from']
                                    tempo = timestamp_converter(int(temp))   
                                    lost = tam - n #timestamp_converter(int(temp))[11:]                                        
                                    n = n + 7 
                                    print('  Loss! '+tempo + ' | n :'+str(n))
                                    loss = loss + 1
                i = n
                break
            else:
                i = i + 1
        return [win,gale,loss,lost]

def getLastBeforeMid(x,today):
    tam = len(x)
    for i in range(tam):
        temp = x[i]['from']
        tempo = timestamp_converter(int(temp))
        if (tempo[12:14] == '23' and tempo[14:16] == '58' and tempo[8:10] != today): #and tempo[8:10] == today):
            return [i,int(temp)]

def getBestOption(x):    
    tam = len(x)
    if(tam == 0):
        print('empty')
        return None
    else:
        paridade = x[0][0]
        temp = x[0][3]
        assertividade = x[0][1]
        for i in range(tam-1):
            if(x[i+1][1] >= assertividade):
                paridade = x[i+1][0]
                temp = x[i+1][3]
                assertividade = x[i+1][1]
        timestamp = temp
        dt_object = datetime.fromtimestamp(timestamp)
        pp = dt_object + timedelta(minutes=6)          
        # print('Proxima entrada - '+str((pp)))
        
        return [paridade,temp,str(pp.strftime("%Y-%m-%d %H:%M:%S")),assertividade]

        

def catalogaR7(update,context):
    update.message.reply_text('Getting R7 Setup Catalog.....')
    par = API.get_all_open() #Get all Open Actives
    tam = 1000
    timeFrame = 60
    initialTime = time.time()
    ini = []
    i = 0
    win = 0
    gale = 0
    loss = 0
    lost = '' 
    to = timestamp_converter(int(initialTime))
    today = str(to[8:10])    
    print(today)
    if par is not None:
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):
            paridade = a[t].upper()
            print(paridade)
            x = API.get_candles(paridade,timeFrame,tam,initialTime)               
            while True:       
                temp = x[i]['from']
                tempo = timestamp_converter(int(temp))            
                if ((tempo[14:16] == '58' and tempo[11:13] >= '00' and tempo[8:10] == today) or (tempo[11:13] == '23' and tempo[14:16] == '58' and tempo[8:10] != today)):                                    
                    n = i
                    while True: 
                        #print(n)
                        if( n+11 > tam):
                            break
                        cor = verifyCandle(x,n,n-1)
                        #print(' Hora : '+str(timestamp_converter(int(x[n]['from'])))+' | Color: '+str(cor))
                        if ( cor == 'Doji'):
                            n = n + 7
                            continue
                        else:
                            if (verifyCandle(x,n+9,n+8) == 'Doji'):
                                n = n + 7 
                                continue
                            else:
                                if (cor == verifyCandle(x,n+9,n+8)):                    
                                    temp = x[n+9]['from']
                                    tempo = timestamp_converter(int(temp))                                    
                                    n = n + 7
                                    print(' win!  '+tempo + ' | n :'+str(n))
                                    win = win + 1
                                else:
                                    if (cor == verifyCandle(x,n+10,n+9)):                        
                                        temp = x[n+10]['from']
                                        tempo = timestamp_converter(int(temp))                                        
                                        n = n + 7
                                        print(' Gale! '+tempo + ' | n :'+str(n))
                                        gale = gale + 1                                                                             
                                    else:                                      
                                        temp = x[n+10]['from']
                                        tempo = timestamp_converter(int(temp))   
                                        lost = tam - n #timestamp_converter(int(temp))[11:]                                        
                                        n = n + 7 
                                        print('  Loss! '+tempo + ' | n :'+str(n))
                                        loss = loss + 1
                    i = n
                    break
                else:
                    i = i + 1
            i = 0
            total = win + gale + loss
            print('Total :'+str(total))
            if(total != 0):
                assertividade = (win+gale)/total
                print('Paridade '+paridade+'| %'+str(assertividade))  
                if(assertividade >= MIN_PROFIT):                                  
                    ini.append([paridade,assertividade,lost,temp])
            total = 0
            win = 0
            gale = 0
            loss = 0

        [escolhido, tempAtual, proximaEntrada, assertividade] = getBestOption(ini)
        #return [escolhido,proximaEntrada]        
        print('escolhido '+escolhido+ ' - Tempo '+str(timestamp_converter(tempAtual))+ ' - Assertividade '+str(round(assertividade*100,2)))
        print('Proxima entrada no final da vela de - '+str(proximaEntrada))
        

def getR7(update, context):
    update.message.reply_text('Getting R7 Setup Catalog.....')
    par = API.get_all_open() #Get all Open Actives 
    pares = []   
    win = 0
    gale = 0
    loss = 0       
    tam = 1000
    if par is not None:
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):
            paridade = a[t].upper()
            x = API.get_candles(paridade,60,tam,time.time())   
            tamX = len(x)
            temp = x[tamX-1]['from']
            tempo = timestamp_converter(int(temp))
            today = str(tempo[8:10])  
            print('Paridade :'+str(paridade)) 
            [w, g, l, lost] = getFirstTime(x,today,win, gale, loss)  
            total = w + g + l
            if(total != 0):
                assertividade = (w+g)/total
                if(assertividade >= MIN_PROFIT):
                    pares.append([paridade,w,g,l,round(assertividade*100,2), str(lost)])
        tamPares = len(pares)
        body = '<<<< Setup R7 >>>>\n\n'
        if(tamPares <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tamPares):
                body = body + '📊'+ str(pares[i][0])  + '('+str(pares[i][4])+')\n✅'+ str(pares[i][1]) + '\n🐔'+ str(pares[i][2]) + '\n❌: '+str(pares[i][3]) +'\nLast loss :'+str(pares[i][5])+' min.\n\n'
        update.message.reply_text(body)
            #print('Win : '+str(w)+'\nGale : '+str(g)+'\nLoss : '+str(l)) 

def getPutSigns(x,today,win, gale, loss):
    i = 0
    lost = 0
    while True:
        #print(i)
        if( i+2 > 1000):
            break
        temp = x[i]['from']
        tempo = timestamp_converter(int(temp))
        if (tempo[12:14] >= '00'): #Verificando somente do dia atual
            if (tempo[14:16] == '00'  and tempo[8:10] == today): #Verificar de parar nessa vela para verificar
            #return temp
                n = i                
                while True:                                        
                    if(x[n]['close'] == x[n]['open']):
                        #print(tempo+ ' === '+str(win)+'x'+str(loss)+' - Doji - '+ str(round((win/(win+loss+0.1))*100,2))+'%')
                        break
                    if(x[n]['close'] > x[n-1]['close'] and x[n+1]['close'] < x[n]['open']):
                        gale = gale + 1
                    if(x[n]['close'] >  x[n-1]['close'] and x[n+1]['close'] > x[n]['open']):                        
                        loss = loss + 1
                        lost = 1000 - n
                        #print(tempo+ ' === '+str(win)+'x'+str(loss)+' - Loss - '+ str(round((win/(win+loss+0.1))*100,2))+'%')
                    if(x[n]['close'] < x[n-1]['close']):                                                
                        win = win + 1
                        #print(tempo+ ' === '+str(win)+'x'+str(loss)+' - Win  - '+ str(round((win/(win+loss+0.1))*100,2))+'%')
                    break           
            i = i + 1
    return [win,gale,loss,lost]

def getForex(update, context):
    update.message.reply_text('Getting Forex Setup Catalog.....')
    # M = ['AUDJPY','AUDUSD','EURAUD','EURJPY','EURUSD','GBPJPY', 'GBPUSD', 'USDJPY',]
    pares = [] 
    par = API.get_all_open() #Get all Open Actives       
    if par is not None:
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):
            paridade = a[t].upper()
    #for i in range(len(M)):
            x = API.get_candles(paridade,300,1000,time.time())   
            tam = len(x)
            temp = x[tam-1]['from']
            tempo = timestamp_converter(int(temp))
            today = str(tempo[8:10])
            win = 0
            loss = 0
            gale = 0 

            [w, g, l,lost] = getPutSigns(x,today, win, gale, loss)
            total = w + l + g
            if(total != 0):
                assertividade = (w+g)/total
                if(assertividade >= MIN_PROFIT):
                    pares.append([paridade,w,g,l,round(assertividade*100,2), str(lost)])
        body = '<<<< Setup FOREX >>>>\n\n'
        tamPares = len(pares)
        if(tamPares <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tamPares):
                body = body + '📊'+ str(pares[i][0])  + '( '+str(pares[i][4])+'% )\n✅'+ str(pares[i][1]) + '\n❌✅'+ str(pares[i][2]) + '\n❌: '+str(pares[i][3]) +'\nLast loss :'+str(pares[i][5])+' min.\n\n'
        update.message.reply_text(body)

        #print('Win : '+str(w)+'\nLoss : '+str(l)+'\n\n')

   
def main():
    """Start the bot."""
    try:
        pid = os.getpid()
    
        updater = Updater(tel.token, use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram    
        dp.add_handler(CommandHandler("setupgg", getGG))
        dp.add_handler(CommandHandler("setupm3", getM3))
        dp.add_handler(CommandHandler("setuptwins", getTwins))    
        dp.add_handler(CommandHandler("setupsequencem1", getMayoritySequenceM1))
        dp.add_handler(CommandHandler("setupr7", getR7 ))
        dp.add_handler(CommandHandler("setupforex", getForex))
        #dp.add_handler(CommandHandler("setupsequencem5", getMayoritySequenceM5))
        #dp.add_handler(CommandHandler("setupsequence30s", getMayoritySequence30s))    
        
    
        updater.start_polling()

        updater.idle()
    except Exception as e:
        print(e)
    
    
if __name__ == '__main__':
    main()
