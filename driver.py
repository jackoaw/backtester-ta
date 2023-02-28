from ta_bruteforce import brute_force_technical_indicators
from tdapi import TDAmeritradeAPI
import os
import pandas as pd
import json

EQ_LIST = [
	'SPY',
	'TSLA',
	'GOOG',
	'XOM'
]

def td_convert(df):
	df = df.rename({
		'open': 'Open',
		'high': 'High',
		'low': 'Low',
		'close': 'Close',
		'volume': 'Volume'
	}, axis=1)
	return df


def main():
	tdapi = TDAmeritradeAPI(os.getenv('TD_API_KEY'))
	for equity in EQ_LIST:
		print('Trading %s'%equity)
		# Get the data
		api_data = json.loads(tdapi.getPrices(
			symbol=equity,
			periodType='year',
			period='5',
			freqType='daily', 
			freqNum='1',
			extendedHours=False
		).content)
		eq_df = td_convert(pd.DataFrame(api_data['candles']))
		eq_df.to_csv('data/' + equity + '.csv')
		# Do the strategy
		brute_force_technical_indicators(equity)

if __name__ == '__main__': 
	main()