import requests

class Quote:
	def __init__(self, lastPrice, bidPrice, askPrice):
		self.last = lastPrice
		self.bid = bidPrice
		self.ask = askPrice

class TDAmeritradeAPI:
	def __init__(self, api_key):
		self.apikey = api_key

	def getPrices(self, symbol, freqType, freqNum, endDate, startDate, extendedHours=True):
		td_ep = "https://api.tdameritrade.com/v1/marketdata/%s/pricehistory" % symbol
		history_params = {
			'apikey':self.apikey,
			'frequencyType': freqType,
			'frequency': freqNum,
			'endDate': endDate,
			'startDate': startDate,
			'needExtendedHoursData': extendedHours
		}
		response = requests.request(method="GET", url = td_ep, params = history_params)
		return response 

	def getQuote(self, symbol):

		td_ep = "https://api.tdameritrade.com/v1/marketdata/%s/quotes" % symbol
		params = {
			'apikey':self.apikey,
		}
		response = requests.request(method="GET", url = td_ep, params = params).json()

		return Quote(
			lastPrice = response[symbol]["lastPrice"],
			askPrice = response[symbol]["askPrice"],
			bidPrice = response[symbol]["bidPrice"]
		) 
		