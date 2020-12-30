import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters,CallbackQueryHandler
from telegram import InlineKeyboardMarkup,InlineKeyboardButton
import csv
from iqoptionapi.stable_api import IQ_Option
import telegram 
from datetime import datetime,timedelta
from time import strftime
import chuckTelegramConfig as tel
import time
from dateutil import tz
from user_config import user
import os
import signal

def getValues():
    # p = str(path.replace('BullRobot',''))
    PATH='user-info.csv'
    with open(PATH, newline='') as csvfile:                
        reader = csv.DictReader(csvfile)
        for row in list(reader):            
            return [str(row['Email']),str(row['Senha']),str(row['Conta'])]
            

# ARRAY_ACTIVES = ['AUDJPY','AUDUSD','AUDCAD','EURAUD','EURGBP','EURJPY','EURUSD','GBPCAD','GBPJPY', 'GBPUSD', 'USDCAD','USDJPY','USDCHF']
# ARRAY_OTC = ['EURUSD-OTC','EURGBP-OTC','USDCHF-OTC','EURJPY-OTC','GBPUSD-OTC','NZDUSD-OTC','AUDCAD-OTC','USDJPY-OTC','GBPJPY-OTC']

MIN_PROFIT = 0.8
M30 = 30
M1 = 60
M5 = 300
MINIMUM_M1 = 30
MININUM_M5 = 30
MINIMUM_30s = 30

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


# def standarFinalDate(data):
#     string = data + HORARIO_FINAL+':00' #"2020-09-18 00:00:00"
#     return time.mktime(datetime.strptime(string,"%Y-%m-%d %H:%M:%S").timetuple())

def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))
    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

def getMinuteFromTimestamp(data):
    return timestamp_converter(data)[14:16]

def verifyCandle(x,actual,past):
    if(x[actual]['close'] == x[past]['open']):
        return 'Doji'
    if(x[actual]['close'] > x[past]['close']):
        return 'Green'
    if(x[actual]['close'] < x[past]['close']):
        return 'Red'

def holdOp(x,win,tam,paridade,ini,API):        
    i = ini
    n = 0
    while (True):
        if(i+2 > tam):
            break
        temp = x[i]['from']
        tempo = timestamp_converter(int(temp))    
        #print(tempo) 
        if (tempo[14:16] == '00' or tempo[14:16] == '30'):
            #print('entrou')
            n = i                          
            while (True ): 
                color = ''                                          
                if(n-6 < 0):
                    antTime = int(x[n]['from'])
                    y = API.get_candles(paridade,300,7,antTime)                    
                    color =  getActualCandleColor(y,0)                    
                else:                    
                    color = getActualCandleColor(x,n-6)
                if(getActualCandleColor(x,n) != color): # Se 1 vela for igual
                    win = win + 1                                        
                    return n
                break           
        i = i + 1
    return n 

def getOperations(x,win, gale, loss,doji,tam,paridade,API):
    i = 0
    message = ''
    while True:
        #print(i)ñ
        if(i+2 > tam):
            break
        temp = x[i]['from']
        tempo = timestamp_converter(int(temp))     
        # print(' --------- '+tempo)   
        if (tempo[14:16] == '00' or tempo[14:16] == '30'): #Verificar de parar nessa vela para verificar
            n = i                          
            while True: 
                color = ''                                          
                if(n-7 < 0):
                    antTime = int(x[n]['from'])
                    #print('opa! '+timestamp_converter(antTime))
                    y = API.get_candles(paridade,300,7,antTime)
                    # p = int(y[0]['from'])
                    # print('Primero! '+timestamp_converter(p))
                    color =  getActualCandleColor(y,0)
                    # print(color)
                else:                    
                    p = int(x[n-6]['from'])
                    print('opa! '+timestamp_converter(p))
                    color = getActualCandleColor(x,n-6)
                # print('Color: '+color)
                # print('Primeira Vela: '+timestamp_converter(x[n]['from'])+' Cor:'+getActualCandleColor(x,n))
                # print('Segunda Vela: '+timestamp_converter(x[n+1]['from'])+ ' Cor: '+getActualCandleColor(x,n+1))
                if(getActualCandleColor(x,n-6) == 'Doji'): # Se a vela do quadrante anterior foi doji -> pula pro proximo                    
                    message = message + str(timestamp_converter(x[n-6]['from'])) + '➕'+ '\n'
                    break
                else:
                    if((getActualCandleColor(x,n) == color) and (getActualCandleColor(x,n+1) != color)): # Se 1 vela for diferente e a segunda for igual
                        message = message + str(timestamp_converter(x[n]['from'])) + '🐔'+ '\n'
                        gale = gale + 1
                    else:
                        if ((getActualCandleColor(x,n) == color) and (getActualCandleColor(x,n+1) == 'Doji')):
                            doji = doji + 1                    
                            message = message + str(timestamp_converter(x[n]['from'])) + '➕❌'+ '\n'                    
                        else:
                            if(((getActualCandleColor(x,n) == color) and (getActualCandleColor(x,n+1) == color))):# Se 1 vela for diferente e a segunda for diferente
                                message = message + str(timestamp_converter(x[n]['from'])) + '❌'+ '\n'
                                loss = loss + 1
                                #print('Loss at '+str(n)+' | '+str(timestamp_converter(x[n]['from'])))
                                #n = holdOp(x,win,tam,paridade,n,API)
                                i = n                
                                #print('Back at '+str(i)+' | '+str(timestamp_converter(x[i]['from'])))
                                # lost = tam - n                    
                            else:    
                                if(getActualCandleColor(x,n) != color): # Se 1 vela for igual
                                    win = win + 1
                                    message = message + str(timestamp_converter(x[n]['from'])) + '✅'+ '\n'
                                    #print(tempo+ ' === '+str(win)+'x'+str(loss)+' - Win  - '+ str(round((win/(win+loss+0.1))*100,2))+'%')
                break           
        i = i + 1
    return [win,gale,loss,doji,message]

def getValActual(w,g,l,d,banca,payout,stake):    
    s = (stake/100) * banca
    p = (payout/100)
    win = (p * s) * w    
    gale = ((2*s)*p - (s))*g   
    doji = l*s*d
    loss = l*(s+(2*s)) 
    return banca + (win + gale - (loss+doji))

def checkLogin():
    resp = ''
    if(user.email == ''):
        resp = resp + ' Email - ' 
    if(user.password == ''): 
        resp = resp + ' Password - '
    if(user.account == ''):
        resp = resp + ' Account'
    if(resp == ''): 
        return False
    else:
        return resp

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

def verifyGG(par,qtd,actualTime,API):    
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
    return [win, g1, loss,lastLoss,message]

def getTimeCandleGG(par,API):
    lastCandles = API.get_candles(par,60,6,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 4):
            return lastCandles[i]['from']

def getGG(update,context,par,qtdVelas,API):
    #update.message.reply_text('Getting GG Setup Catalog.....')                  
    paridade = par.upper() # Caps Lock                      
    actualTimeGG = int(getTimeCandleGG(paridade,API))
    [wn, g, loss,lastLoss,message] =  verifyGG(paridade,qtdVelas,actualTimeGG,API)
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

def checkM3(arr,win,g1,loss):
    try:
        w = win
        g = g1
        l = loss
        print('Check')
        for i in reversed(range(len(arr))):
            candle = getActualCandleColor(arr,i)
            if(candle == 'Doji'):
                return [w,g,l,'-']

        print('Check Assigntment')    
        firstCandle = getActualCandleColor(arr,1)
        secondCanle = getActualCandleColor(arr,2)
        thirdCandle = getActualCandleColor(arr,3)
        fourthCandle = getActualCandleColor(arr,4)
        fifthCandle = getActualCandleColor(arr,5)
        sixthCandle = getActualCandleColor(arr,6)

        print('Check Pattern')
        message = ''
        if(firstCandle != secondCanle):
            if(thirdCandle == fourthCandle and fourthCandle == fifthCandle):
                if(sixthCandle == fifthCandle):
                    w = w + 1
                    message = message + timestamp_converter(arr[1]['from']) + ' ✅\n'
                    #print('Win - '+timestamp_converter(arr[1]['from'])+' -> '+str(timestamp_converter(arr[0]['from'])+' -> '+str(timestamp_converter(arr[5]['from']))))
                    return [w,g,l,'-',message]
                else:
                    l = l + 1 
                    message = message + timestamp_converter(arr[1]['from']) + ' ❌\n'
                    #print('Loss - '+timestamp_converter(arr[1]['from'])+' -> '+str(timestamp_converter(arr[0]['from'])+' -> '+str(timestamp_converter(arr[5]['from']))))
                    return [w,g,l,'x',message]
                
        return [w,g,l,'-',message]
    except Exception as e: 
        print(e)

def verifyM3(par,qtd,actualTime,API):    
    try:
        confirm = True
        win = 0
        g1 = 0
        loss = 0
        cont = 0 
        entra = True
        lastLoss = ''
        message = ''
        print('VerifyM3')
        while confirm:
            x = API.get_candles(par,60,7,actualTime)   
            print(x)
            result = checkM3(x,win,g1,loss)
            win = result[0]
            g1 = result[1]
            loss = result[2] 
            message = result[4] + message
            print(message)
            if(cont == qtd):#strTime <= timestamp_converter(standarIniDate(data))):
                confirm = False      
            if(result[3] != '-' and entra == True):
                lastLoss = timestamp_converter(x[1]['from'])[11:]
                #print('Loss - '+timestamp_converter(x[1]['from']))
                entra = False
            cont = cont + 1
            actualTime = x[1]['from']

        #p = win + g1 + loss
        wn = win + g1
        return [wn, loss,lastLoss,message]
    except Exception as e:
        print(e)
    # header = '******** Setup M3 ********\n\n📊 '+par
    # body = '\n✅Win: '+ str(float(wn))+ '\n❌Loss: '+str(loss)+'\n\n Ultimo Loss: '+str(lastLoss)+'\n'
    
    # time.sleep(3)
    # update.message.reply_text(header+body)

def getTimeCandleM3(par,API):
    lastCandles = API.get_candles(par,60,7,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 0):
            #print(timestamp_converter(lastCandles[0]['from']))
            return lastCandles[i]['from']

def getM3(update,context,par,qtdVelas,API):    
    if par is not None: 
        try:                       
            paridade = par.upper() # Caps Lock 
            actualTimeM3 = int(getTimeCandleM3(paridade,API))
            [wn, loss,lastLoss,message] =  verifyM3(paridade,qtdVelas,actualTimeM3,API)
            if(wn + loss != 0):
                banca = 1000        
                payout = 80
                stake = 5
                resultado = round(getValActual(wn,0,loss,0,banca,payout,stake),2)
                #simulation = 'Positivo' if resultado > banca else 'Empatou' if resultado == banca else 'Negativo'
                body = '\n\nSimulaçao de valores\nBanca: '+str(banca)+'\nStake: '+str(stake)+'%\nPayout: '+str(payout)+'%\n'+'Banca Final:'+str(resultado)
            else:
                body = 'Nao aconteceu nenhuma operacao nessa operacao'
            header = '<<<< BACKTEST M3 - '+str(paridade)+' >>>>\n\n'        
            body = header + message + body#'📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
            update.message.reply_text(body)
        except Exception as e:
            print(e)
        

def getTimeCandleTwins(par,API):
    lastCandles = API.get_candles(par,60,6,time.time())
    tam = len(lastCandles)
    for i in reversed(range(tam)):
        tm = int(getMinuteFromTimestamp(lastCandles[i]['from']))
        if(tm%5 == 4):
            #print(timestamp_converter(lastCandles[i]['from']))
            return lastCandles[i]['from']

def checkEngolfo(arr,first,second):
    firstColor = getActualCandleColor(arr,first)
    if(firstColor == 'Green'):
        return arr[second]['close'] <= arr[first]['open']
    if(firstColor == 'Red'):
        return arr[second]['close'] >= arr[first]['open']

def checkTwins(arr,win,g1,loss):
    w = win
    g = g1
    l = loss
    for i in range(6):
        candle = getActualCandleColor(arr,i)
        if(candle == 'Doji'):
            return [w,g,l,'-']
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
                        #print('Win - '+timestamp_converter(arr[1]['from']))
                        return [w,g,l,'-']
                    else:
                        l = l + 1 
                        #print('Loss - '+timestamp_converter(arr[1]['from']))
                        return [w,g,l,'x']
               
    return [w,g,l,'-']

def verifyTwins(par,actualTime,API):    
    confirm = True
    win = 0
    g1 = 0
    loss = 0
    cont = 0 
    entra = True
    lastLoss = ''

    
    while confirm:
        x = API.get_candles(par,60,6,actualTime)   
        #print(timestamp_converter(x[5]['from'])[11:])
        result = checkTwins(x,win,g1,loss)
        win = result[0]
        g1 = result[1]
        loss = result[2] 
        if(cont == MINIMUM_M1):#strTime <= timestamp_converter(standarIniDate(data))):
            confirm = False      
        if(result[3] != '-' and entra == True):
            lastLoss = timestamp_converter(x[1]['from'])[11:]
            #print('Loss - '+timestamp_converter(x[1]['from']))
            entra = False
        cont = cont + 1
        actualTime = x[0]['from']

    #p = win + g1 + loss
    wn = win + g1
    return [wn, loss,lastLoss]

def getTwins(update,context,par,qtdVelas,API):
    update.message.reply_text('Getting Twins Setup Catalog.....')
    par = API.get_all_open() #Get all Open Actives 
    pares = []            
    if par is not None:                
        a = getActiveDigital(par) # Filter Digital Open Actives            
        for t in range(len(a)):   
            paridade = a[t].upper() # Caps Lock
            actualTimeTwins = int(getTimeCandleTwins(paridade,API))
            [wn, loss,lastLoss] =  verifyTwins(paridade,actualTimeTwins,API)
            total = wn + loss
            if(total != 0):
                assertividade = wn/total
                if(assertividade >= MIN_PROFIT):
                    pares.append([paridade,wn,loss,round(assertividade*100,2),lastLoss])
        tamPares = len(pares)
        body = '<<<< Setup Twins >>>>\n\n'
        if(tamPares <= 0):
            body = 'Nao aconteceu este padrao !!'
        else:
            for i in range(tamPares):
                body = body + '📊'+ str(pares[i][0]) + ' - ' + str(pares[i][3]) + '%\n✅'+ str(pares[i][1]) + '❌'+ str(pares[i][2]) + '\nLast Loss: '+str(pares[i][4]) +'\n\n'
        update.message.reply_text(body) 

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

def getR7(update, context,par,qtdVelas,API):
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

def getVader(update,context,paridade,qtdVelas,API):
    if paridade is not None:        
        x = API.get_candles(paridade,300,6*(qtdVelas),time.time())  
        tam = len(x)         
        win = 0
        loss = 0
        gale = 0 
        doji = 0

        [w, g, l,doji,message] = getOperations(x, win, gale, loss, doji,tam,paridade,API)
        banca = 1000        
        payout = 80
        stake = 5
        resultado = round(getValActual(w,g,l,doji,banca,payout,stake),2)
        header = '<<<< BACKTEST VADER - '+str(paridade)+'>>>>\n\n'
        simulation = 'Positivo' if resultado > banca else 'Empatou' if resultado == banca else 'Negativo'
        body = '\n\nSimulaçao de valores\nBanca: '+str(banca)+'\nStake: '+str(stake)+'%\nPayout: '+str(payout)+'%\n'+'Banca Final:'+str(resultado)
        update.message.reply_text(header+'Backtest '+str(paridade)+'\n\n'+str(message)+str(body)+'\nStatus: '+str(simulation))        
        
def catalogar(update, context):
    resp = update['message']['text'].split(' ')
    setup = str(resp[1].lower())
    paridade = str(resp[2].upper())
    qtdVelas = int(resp[3])   
    login = checkLogin()
    if(login):
        update.message.reply_text('Faltam preencher o(s) campo(s):'+str(login))
    else:
        API = IQ_Option(user.email,user.password)
        API.connect()
        API.change_balance(user.account.upper())

        check(API)
        if(setup.upper() == 'VADER'):
            getVader(update,context,paridade,qtdVelas,API)            
        if(setup.upper() == 'GG'):
            # getGG(update,context,paridade,qtdVelas,API)    
            update.message.reply_text('SETUP GG EM CONSTRUCAO!')
        if(setup.upper() == 'M3'):
            update.message.reply_text('SETUP M3 EM CONSTRUCAO!')
            #getM3(update,context,paridade,qtdVelas,API)
        if(setup.upper() == 'R7'):
            update.message.reply_text('SETUP R7 EM CONSTRUCAO!')
            # getR7(update,context,paridade,qtdVelas,API)
        if(setup.upper() == 'TWINS'):
            update.message.reply_text('SETUP TWINS EM CONSTRUCAO!')
            # getTwins(update,context,paridade,qtdVelas,API)
        if(setup.upper() == 'FR'):
            update.message.reply_text('SETUP FR EM CONSTRUCAO!')

## CONFIG ##
def setTipo(update, context):
    tipo  = str(update['message']['text'].split(' ')[1])
    user.setTipo(tipo)
    update.message.reply_text('Operaçoes irao executar em pares do tipo: '+str(user.tipo))

def setEmail(update, context):          
    email  = str(update['message']['text'].split(' ')[1])
    user.setEmail(email)
    update.message.reply_text('Email alterado com sucesso!')

def setAccount(update, context):           
    account  = str(update['message']['text'].split(' ')[1])
    user.setAccount(account)
    update.message.reply_text('Tipo de conta alterada com sucesso!')

def setPassword(update, context):           
    password  = str(update['message']['text'].split(' ')[1])
    user.setPassword(password)
    update.message.reply_text('Senha alterada com sucesso!')

def setGale(update, context):        
    gale  = float(update['message']['text'].split(' ')[1])    
    user.setGale(gale)
    update.message.reply_text('Multiplicador do gale alterado com sucesso!')

def setCiclo(update, context):        
    ciclo  = int(update['message']['text'].split(' ')[1])
    user.setCiclo(ciclo)
    if(user.ciclo != 0):
        update.message.reply_text('Ciclo ativado com sucesso!')
    if(user.ciclo == 0):
        update.message.reply_text('Ciclo desativado com sucesso!')

def setStopWin(update, context):        
    valor  = float(update['message']['text'].split(' ')[1])
    user.setStopWin(valor)
    update.message.reply_text('Stop Win alterado com sucesso!')

def setStopLoss(update, context):        
    valor  = float(update['message']['text'].split(' ')[1])
    user.setStopLoss(valor)
    update.message.reply_text('Stop Loss alterado com sucesso!')

def setPayout(update, context):        
    payout  = float(update['message']['text'].split(' ')[1])    
    user.setPayout(payout)
    update.message.reply_text('Payout alterado com sucesso!')

def setStake(update, context):        
    valor  = float(update['message']['text'].split(' ')[1])
    user.setStake(valor)
    update.message.reply_text('Stake alterado com sucesso!')

def verifyIfHasValues(filename, ext):
    PATH= filename+ext
    results = []
    with open(PATH, newline='') as csvfile:                
        reader = csv.DictReader(csvfile)
        for row in list(reader): 
            results.append(str(row['Conta']))
            results.append(str(row['Tipo'])) 
            results.append(int(row['Ciclo'])) 
            results.append(str(row['Email'])) 
            results.append(str(row['Senha']))
            results.append(float(row['BIni']))
            results.append(float(row['BAtual'])) 
            results.append(float(row['StopW']))
            results.append(float(row['StopL']))
            results.append(float(row['Gale']))
            results.append(str(row['Setup']))
            results.append(float(row['Payout']))
            results.append(str(row['Ativo']))
            results.append(float(row['Stake']))
            results.append(int(row['Status']))            
    return results


def writeUserInfo():
    try:
        fileName = 'user-info'
        extension='csv'            
        # resp = verifyIfHasValues(fileName,extension)
        # if(len(resp) != 0):
        #     user.setAccount(str(resp[0]))
        #     user.setTipo(str(resp[1]))
        #     user.setCiclo(int(resp[2]))
        #     user.setEmail(str(resp[3]))
        #     user.setPassword(str(resp[4]))
        #     user.setIniBalance(float(resp[5]))
        #     user.setBalance(float(resp[6]))
        #     user.setStopWin(float(resp[7]))
        #     user.setStopLoss(float(resp[8]))
        #     user.setGale(float(resp[9]))
        #     user.setSetup(str(resp[10]))
        #     user.setPayout(float(resp[11]))
        #     user.setPair(str(resp[12]))
        #     user.setStake(float(resp[13]))
        #     user.on = int(resp[14])
        # else:
        with open('%s.%s'%(fileName,extension),'w+',newline='') as f:
                fieldnames= ['Conta','Tipo','Ciclo','Email','Senha','BIni','BAtual','StopW','StopL','Gale','Setup','Payout','Ativo','Stake','Status']
                theWriter= csv.DictWriter(f,fieldnames=fieldnames)
                if f.tell() == 0:
                    theWriter.writeheader()                
                theWriter.writerow(
                    {                        
                        'Conta':str(user.account.upper()),
                        'Tipo': str(user.tipo.lower()),
                        'Ciclo': str(user.ciclo),
                        'Email': str(user.email),
                        'Senha': str(user.password),
                        'BIni': float(user.iniBalance),
                        'BAtual': float(user.actualBalance),
                        'StopW': float(user.stopwin),
                        'StopL': float(user.stoploss),
                        'Gale': float(user.gale),
                        'Payout': int(user.payout),
                        'Setup': str(user.setup.upper()),
                        'Ativo': str(user.pair.upper()),
                        'Stake': str(user.stake),
                        'Status': str(user.on)
                    }
                )
        return
    except Exception as e:
        print(e)

def setActive(update, context):
    ativo  = str(update['message']['text'].split(' ')[1])
    user.setPair(ativo)
    update.message.reply_text('Ativo alterado com sucesso!')

def getActives(update, context):
    login = checkLogin()
    update.message.reply_text('Pegando paridades ativas!')
    if(login):
        update.message.reply_text('Faltam preencher o(s) campo(s):'+str(login))
    else:
        API = IQ_Option(user.email,user.password)
        API.connect()
        API.change_balance(user.account.upper())

        check(API)
        message = '📊 Paridades Ativas 📊\n\n Tipo: '+str(user.tipo.lower()) + '\n\n'    
        pares = API.get_all_open_time_v2() #Verificar isso  
        if pares is not None:
            a = pares[user.tipo.lower()]
            for i in range(len(a)):             
                message = message + '🔸 ' +str(a[i].upper()) + '\n'                
            update.message.reply_text(message)

def empty():
    resp = ''
    if(user.email == ''):
        resp = resp + ' Email - ' 
    if(user.password == ''): 
        resp = resp + ' Password - '
    if(user.account == ''):
        resp = resp + ' Account - '
    if(user.tipo == ''):
        resp = resp + ' Tipo - '
    if(user.gale == 0.0):
        resp = resp + ' Gale - '
    if(user.stopwin == 0.0):
        resp = resp + ' StopWin - '
    if(user.stoploss == 0.0):
        resp = resp + ' StopLoss - '
    if(user.pair == ''):
        resp = resp + ' Active - '
    if(user.payout == 0):
        resp = resp + ' Payout - '
    if(user.stake == 0.0):
        resp = resp + ' Stake - '
    if(user.setup == ''):
        resp = resp + ' Setup'
    if(resp == ''): 
        return False
    else:
        return resp

def updateInfo(update, context):
    vals = empty()     
    if(vals):    
        update.message.reply_text('Faltam preencher o(s) campo(s):'+str(vals))
    else:
        user.on = 1
        writeUserInfo()
        update.message.reply_text('Informações atualizadas com sucesso!')

def setSetup(update, context):
    setup  = str(update['message']['text'].split(' ')[1])
    user.setSetup(setup)
    update.message.reply_text('Setup '+str(setup)+' definido com sucesso!')


## OPERACIONAL ##
def startBot(update, context):  
    if(user.on == 0):
        update.message.reply_text('Rode o comando update antes de iniciar!')
    if(user.on == 1):   
        try: 
            login = checkLogin()
            if(login):
                update.message.reply_text('Faltam preencher o(s) campo(s):'+str(login))
            else:
                API = IQ_Option(user.email,user.password)
                API.connect()
                API.change_balance(user.account.upper())                
                check(API) 
                actualVal = float(API.get_balance())
                print(actualVal)   
                user.setBalance(actualVal)
                user.setIniBalance(actualVal)                     
                updateInfo(update,context) #Atualizando informacoes   
                update.message.reply_text(str('Running....'))
                time.sleep(3)
                os.system('nohup python3 ./Chuck/chuckBot.py &')
        except Exception as e:
            update.message.reply_text(str(e))

def getBotInfo(update):
    try:
        cwd = str(os.getcwd())[0:17]        
        print(cwd)
        PATH= cwd + '/bot-status.csv'                   
        with open(PATH, newline='') as csvfile:                
            reader = csv.DictReader(csvfile)
            for row in reversed(list(reader)):                  
                return [int(row['Pid']),float(row['IniBalance'])]
    except Exception as e:
         update.message.reply_text(str(e))


def showReport(update):
    try:
        header = ''
        login = checkLogin()
        if(login):
            update.message.reply_text('Faltam preencher o(s) campo(s):'+str(login))
        else:
            API = IQ_Option(user.email,user.password)
            API.connect()
            API.change_balance(user.account.upper())
            check(API) 
            actual = API.get_balance()
            print(actual)
            perc = round(((actual/user.iniBalance) -1 )*100,2)
            if(user.on == 0):
                body = 'Bot has not started today yet!'
            else:
                header = '   💰 - Chuck Report - 💰\n\n'
                body = 'Initial Balance: R$ '+str(user.iniBalance)+'\nActual Balance: R$ '+str(API.get_balance())+'\n\n Profit: '+str(perc)+'%'
            update.message.reply_text(header+body)
    except Exception as e:
        update.message.reply_text(str(e))

def deletingProcess(update):
    try:
        values = getBotInfo(update)    
        os.kill(int(values[0]),signal.SIGKILL)
        #os.remove('nohup.out')
        showReport(update,)
    except Exception as e:
         update.message.reply_text(str(e))  


def stopBot(update, context):  
    # header = '🎉 Chuck Bot has reach his goal! 🎉\nCongratulations!\n\n'
    # body = '💰 Banca Inicial: '+str(user.iniBalance)+'\nBanca Atual: '+str(user.actualBalance)+'\n💸 Profit: '+str(user.getProfit())+' '+str(user.coinSymbol)
    if(user.on == 0):
        update.message.reply_text('O seu robo ja esta desligado.....')         
    else:
        user.setOffline()
        updateInfo(update,context)
        update.message.reply_text('Turning off your bot.....')     
        time.sleep(3)
        deletingProcess(update)
        update.message.reply_text('Your Bot is finally off')   
    
def getReport(update, context):    
    showReport(update)

def getInfo(update, context):            
    update.message.reply_text(str(user))



def main():
    """Start the bot."""
    try:
        pid = os.getpid()
    
        updater = Updater(tel.token, use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        
        
        # on different commands - answer in Telegram    
        dp.add_handler(CommandHandler("update", updateInfo))
        dp.add_handler(CommandHandler("catalogar", catalogar))
        dp.add_handler(CommandHandler("setup", setSetup))
        dp.add_handler(CommandHandler("getinfo", getInfo))
        dp.add_handler(CommandHandler("startbot", startBot))
        dp.add_handler(CommandHandler("stopbot", stopBot))
        dp.add_handler(CommandHandler("getreport", getReport))
        dp.add_handler(CommandHandler("tipo", setTipo))
        dp.add_handler(CommandHandler("email", setEmail))
        dp.add_handler(CommandHandler("conta", setAccount))    
        dp.add_handler(CommandHandler("senha", setPassword))
        dp.add_handler(CommandHandler("gale", setGale))
        dp.add_handler(CommandHandler("ciclo", setCiclo))
        dp.add_handler(CommandHandler("stopwin", setStopWin))        
        dp.add_handler(CommandHandler("stoploss", setStopLoss))
        dp.add_handler(CommandHandler("payout", setPayout))
        dp.add_handler(CommandHandler("stake", setStake))
        dp.add_handler(CommandHandler("paridade", setActive))
        dp.add_handler(CommandHandler("ativosabertos", getActives))
        
        updater.start_polling()

        updater.idle()
    except Exception as e:
        print(e)


def check(API):
    while True:
        if API.check_connect() == False:        
            #print('Erro ao se conectar!')    
            API.connect()    
        else:
            #print('Conectado com sucesso! '+str(os.getpid()))
            break

if __name__ == '__main__':
    main()

