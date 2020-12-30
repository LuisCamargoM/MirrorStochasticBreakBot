
class User:
    def __init__(self):        
        self.on = 0
        self.tipo = ''        
        self.email = ''
        self.account  = ''
        self.password = ''        
        self.coinSymbol = ''
        self.gale = 0.0
        self.ciclo = 0  
        self.iniBalance = 0.0
        self.actualBalance = 0.0
        self.stopwin = 0.0
        self.stoploss = 0.0
        self.pair = ''
        self.name = ''
        self.payout = 0.0     
        self.id = ''
        self.stake = 0.0
        self.setup = ''

    def __str__(self):
        try:            
            perfil = "✉️ Emaill: {self.email}\n"
            conta = "🔘 Tipo: {self.tipo}\n🗳 Conta: {self.account}\n"
            op = "📊 Paridade: {self.pair}\n📝 Setup: {self.setup}\n✅ Stop Win: {self.stopwin} %\n❌ Stop Loss: {self.stoploss} %\n🅿️ Payout: {self.payout} %\n💰 Stake: {self.stake}\n♻️ Gale: {self.gale}\n🌀 Ciclo: {self.ciclo}\n"
            status = "💡 Status: {self.on}"
            return str(perfil+conta+op+status).format(self=self)
        except Exception as e:
            print(e)  

    def setSymbol(self):
        try:
            if(self.account == 'REAL'):
                self.coinSymbol = 'R$'
            if(self.account == 'PRACTICE'):
                self.coinSymbol = '$'
            if(self.account == ''):
                self.coinSymbol = ''
        except Exception as e:
            print(e)

    def setStake(self,val):
        try:
            assert isinstance(val, float)
            self.stake = val
        except Exception as e:
            print(e)
    
    def setSetup(self,setup):
        try:
            assert isinstance(setup, str)
            self.setup = setup.upper()
        except Exception as e:
            print(e)

    def setPayout(self,val):
        try:
            assert isinstance(val, float)
            self.payout = val
        except Exception as e:
            print(e)
            
    def clearFields(self):
        try:
            self.on = 0
            self.tipo = ''        
            self.email = ''
            self.account  = ''
            self.password = ''            
            self.coinSymbol = ''
            self.gale = 0.0
            self.ciclo = 0  
            self.iniBalance = 0.0
            self.actualBalance = 0.0
            self.stopwin = 0.0
            self.stoploss = 0.0
            self.pair = ''
            self.name = ''
            self.payout = 0        
            self.id = ''
            self.stake = 0.0
            self.setup = ''

        except Exception as e:
            print(e) 

    def setTipo(self,lang):
        try:
            assert isinstance(lang, str)
            if(lang.lower() == 'binaria'):
                self.tipo = 'TURBO'
            if(lang.lower() == 'digital'):
                self.tipo = lang.upper()
        except Exception as e:
            print(e)

    def setPair(self,lang):
        try:
            assert isinstance(lang, str)
            self.pair = lang.upper()
        except Exception as e:
            print(e)        
    
    def setOnline(self):
        try:
            self.on = 1
        except Exception as e:
            print(e)      
    
    def setOffline(self):
        try:
            self.on = 0
        except Exception as e:
            print(e)   
    
    def setID(self, lang):
        try:
            assert isinstance(lang, str)
            self.id = lang
        except Exception as e:
            print(e)  

    def setName(self, lang):
        try:
            assert isinstance(lang, str)
            self.name = lang
        except Exception as e:
            print(e)    
    
    def setEmail(self, lang):
        try:
            assert isinstance(lang, str)
            self.email = lang
        except Exception as e:
            print(e)    
    
    def setPassword(self, lang):
        try:
            assert isinstance(lang, str)
            self.password = lang
        except Exception as e:
            print(e)    

    def validateBot(self, lang):
        try:
            token = str(self.password)+'2020'
            if(str(lang) == '' or str(lang) == ' '):
                return [False,'Empty Field']
            if(str(lang) == token):
                return [True,'Token validated!']
            return [False,'Token incorrect']
        except Exception as e:
            print(e)

    def setAccount(self, lang):        
        try:
            assert isinstance(lang, str)
            if(lang.lower() == 'treinamento'):
                self.account = 'Practice'
            if(lang.lower() == 'real'):
                self.account = 'Real'                
        except Exception as e:
            print(e)        
    
    def setGale(self, lang):
        try:
            assert isinstance(lang, float)
            self.gale = lang
        except Exception as e:
            print(e)    
    
    def setCiclo(self, lang):
        try:
            assert isinstance(lang, int)
            self.ciclo = lang
        except Exception as e:
            print(e)    

    def setBalance(self, lang):
        try:
            assert isinstance(lang, float)
            self.actualBalance = lang
        except Exception as e:
            print(e)
            
    def setIniBalance(self,lang):
        try:
            assert isinstance(lang,float)
            self.iniBalance = lang
        except Exception as e:
            print(e)    

    def getProfit(self):
        try:
            profit = self.actualBalance - self.iniBalance
            return float(profit)
        except Exception as e:
            print(e)    

    def getProfitPercent(self):
        try:
            if (self.iniBalance == 0.0 ):
                return -1
            profit = self.actualBalance - self.iniBalance
            return float(round((profit/self.actualBalance)*100,2))
        except Exception as e:
            print(e)    

    def setStopWin(self,val):
        try:
            assert isinstance(val,float)
            self.stopwin = val
        except Exception as e:
            print(e)    

    def setStopLoss(self,val):
        try:
            assert isinstance(val,float)
            self.stoploss = val
        except Exception as e:
            print(e)    

user = User()
