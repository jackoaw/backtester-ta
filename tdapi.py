import requests
from datetime import datetime

class Quote:
	def __init__(self, lastPrice, bidPrice, askPrice):
		self.last = lastPrice
		self.bid = bidPrice
		self.ask = askPrice

class TDAmeritradeAPI:
	def __init__(self, api_key):
		self.apikey = api_key

	# Accepted format for dates is MM/DD/YYYY
	def getPricesFromDates(self, symbol, freqType, freqNum, startDate, endDate, extendedHours=True):
		td_ep = "https://api.tdameritrade.com/v1/marketdata/%s/pricehistory" % symbol

		startDate = datetime.strptime(startDate, "%m/%d/%Y")
		startDate = int(startDate.timestamp()*1000) #to miliseconds
		endDate = datetime.strptime(endDate, "%m/%d/%Y")
		endDate = int(endDate.timestamp()*1000) #to miliseconds
		print(startDate)
		print(endDate)

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

	# Accepted format for dates is MM/DD/YYYY
	def getPrices(self, symbol, periodType, period, freqType, freqNum, extendedHours=True):
		td_ep = "https://api.tdameritrade.com/v1/marketdata/%s/pricehistory" % symbol

		history_params = {
			'apikey':self.apikey,
			'periodType':periodType,
			'period':period,
			'frequencyType': freqType,
			'frequency': freqNum,
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
