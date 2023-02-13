import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna
import np
from multiprocessing import Process

global_starting_money = 10000

class Strategy:

	def __init__(self, 
		name,
		conditions, 
		# close_conditions, 
		starting_money=global_starting_money,
		risk_percent=.2,
		open_args={},
		close_args={}):

		# self.longcs = long_conditions
		# self.shortcs = short_conditions
		self.conditions = conditions
		self.openclose = conditions
		self.account = Account(starting_money, risk_percent)
		self.open_args = open_args
		self.close_args = close_args
		self.name = name
		self.percent_change = 0
		# self.currentLong

	def act(self, i, row):
		# Start with just one long and short condition for now.
		if self.conditions[0](row, i, self.open_args):
			if self.open_args['buy']:
				self.account.buy(row['Close'])
			else:
				self.account.sell(row['Close'])
		elif self.conditions[1](row, i, self.close_args):
			if self.close_args['buy']:
				self.account.buy(row['Close'])
			else:
				self.account.sell(row['Close'])


class Account:

	def __init__(self, money, riskpertrade):
		# Money as an int
		self.money = money
		# Risk as a decimal less than 1
		self.risknum = riskpertrade
		# How many shares is being longed or shorted
		self.holdnum = 0

	def buy(self, price, risknum=0):
		risknum = self.risknum if risknum==0 else .2
		# If long already do nothing
		if self.holdnum > 0:
			return
		# If short, close
		elif self.holdnum < 0:
			self.money -= (price*self.holdnum*-1)
			# print("Closed %i shares at price %f"%(self.holdnum, price))
			self.holdnum = 0
		# Else start long
		else:
			buyammount = int((self.money*risknum)/price)
			self.money -= (price*buyammount)
			self.holdnum = buyammount
			# print("Bought %i shares at price %f"%(buyammount, price))
		# print("Money: %f"%self.money)


	def sell(self, price, risknum=0):
		risknum = self.risknum if risknum==0 else .2
		# If short already do nothing
		if self.holdnum < 0:
			return
		# If long, close
		elif self.holdnum > 0:
			self.money += (price*self.holdnum)
			# print("Closed %i shares at price %f"%(self.holdnum, price))
			self.holdnum = 0
		# Else start short
		else:
			buyammount = int(((self.money*risknum)/price))
			self.money += (price*buyammount)
			self.holdnum = buyammount*-1
			# print("Sold %i shares at price %f"%(buyammount, price))

		# print("Money: %f"%self.money)


# Needs arg 
# rsinum
# lt TRUE or FALSE
def rsi(row, i, args={}, **kwargs):
	if args['lt']:
		if row['momentum_rsi'] <= args["rsinum"]:
			return True
	else:
		if row['momentum_rsi'] >= args["rsinum"]:
			return True
	return False


def ema_slow(row, i, args={}, **kwargs):	
	if row.isna()['trend_ema_slow'] is True:
		return False
	if not args['above']:
		if row['Close'] <= row["trend_ema_slow"]:
			return True
	else:
		if row['Close'] >= row["trend_ema_slow"]:
			return True
	return False

# Combo one buy method with one sell method?

def execute_strategy(strat, df):
	# First the trading
	lastrow = None
	for i, row in df.iterrows():
		strat.act(i, row)
	lastrow = row

	# Then the summary
	if strat.account.holdnum > 0:
		strat.account.sell(lastrow['Close'])
	elif strat.account.holdnum < 0:
		strat.account.buy(lastrow['Close'])

	# Define Success here
	strat.percent_change = (strat.account.money/global_starting_money - 1)*100
	if strat.percent_change >= 1:
		return True

	return False



def main():
	# Load datas
	df = pd.read_csv('SPY.csv', sep=',')

	# Clean NaN values
	df = dropna(df)

	# Add all ta features
	df = add_all_ta_features(
		df, open="Open", high="High", low="Low", close="Close", volume="Volume"
	)

	strats = []

	# Form all of the RSI Trades
	for x in range(0,100):
		for y in range(0,100):
			strats.append(
				Strategy("RSI Buy %i Sell %i"%(y, x), (rsi, rsi), open_args={"rsinum":x, 'lt':True, 'buy':False}, close_args={"rsinum":y, 'lt':False, 'buy':True})
			)


	# Form all of the strategies here
	strats_example = [
		Strategy("RSI High", (rsi, rsi), open_args={"rsinum":70, 'lt':True, 'buy':False}, close_args={"rsinum":60, 'lt':False, 'buy':True}),
		Strategy("RSI Low", (rsi, rsi), open_args={"rsinum":30, 'lt':True, 'buy':True}, close_args={"rsinum":60, 'lt':False, 'buy':False}),
		Strategy("Slow EMA Trade", (ema_slow, ema_slow), open_args={"above":False, 'buy':False}, close_args={"above":True, 'buy':True})
	]

	success_strategies = []

	# Cycle through buy_methods and check success rate
	for strat in strats_example:
		if execute_strategy(strat, df):
			success_strategies.append(strat)

	sorted_success_strategies = sorted(success_strategies, key=lambda x: x.account.money, reverse=True)

	for strat in success_strategies:
		print("Strategy %s generated a %0.2f%% return"% (strat.name, strat.percent_change))

	# Final step is to close all account positions, or just report the total


main()
