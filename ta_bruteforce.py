import pandas as pd
from copy import copy
from ta import add_all_ta_features
from ta.utils import dropna
import np
from multiprocessing import Process, Pool
import sys
import warnings
warnings.filterwarnings("ignore")
from itertools import chain, combinations

global_starting_money = 10000
MULTICORE = False
CORS_NUM = 12
TESTMODE = False

save_results_map = {}


# Condition class is AND by default, combining these is an OR
class Condition:

	def __init__(self, conditions : list, buy):
		self.conditions = conditions
		self.buy = buy

	def isTrue(self, row, i):
		for strat, cond_args in self.conditions.items():
			if not strat(row, i, cond_args):
				return False
		return True

	# If it's a sell, then this will return False
	def isBuy(self):
		return self.buy



class Strategy:

	def __init__(self, 
		name,
		open_condition,
		close_condition,
		starting_money=global_starting_money,
		risk_percent=.2
		):

		self.open_condition = open_condition
		self.close_condition = close_condition
		self.account = Account(starting_money, risk_percent)
		self.name = name
		self.percent_change = 0
		self.trade_count = 0
		# self.currentLong

	def act(self, i, row):
		# Start with just one long and short condition for now.
		if self.open_condition.isTrue(row, i):
			if self.open_condition.isBuy():
				self.account.buy(row['Close'])
			else:
				self.account.sell(row['Close'])
			self.trade_count += 1
		elif self.close_condition.isTrue(row, i):
			if self.close_condition.isBuy():
				self.account.buy(row['Close'])
			else:
				self.account.sell(row['Close'])
			self.trade_count += 1


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

	# Then the Closing
	if strat.account.holdnum > 0:
		strat.account.sell(lastrow['Close'])
	elif strat.account.holdnum < 0:
		strat.account.buy(lastrow['Close'])

	# Define Success here
	strat.percent_change = (strat.account.money/global_starting_money - 1)*100

	# if False:
	# 	return strat
	# else:
	# Have at least two trades
	if strat.percent_change >= 1 and strat.trade_count/2 > 2:
		# print("Strategy %s generated a %0.2f%% return"% (strat.name, strat.percent_change))
		print('w', end='', flush=True)
		return True
	else:
		print('f', end='', flush=True)
		return False


from itertools import chain, combinations
def all_subsets(ss):
    return chain(*map(lambda x: combinations(ss, x), range(0, len(ss)+1)))


def form_strats():
	strats = []

	# Variable methods
	open_ta_possibilities = [
		rsi,
		ema_slow	
	]

	# Form all the variations of the above methods
	all_strat_variations = {}
	for strat_method in open_ta_possibilities:
		strat_name = strat_method.__qualname__
		if strat_name == "rsi":
			all_strat_variations['rsi'] = []
			for boolean in [True, False]:
				for x in range(10,90):
					all_strat_variations['rsi'].append(
						(rsi, {"rsinum":x, 'lt':boolean})
					)
		elif strat_name == "ema_slow":
			all_strat_variations['ema_slow'] = []
			for boolean in [True, False]:
				all_strat_variations['ema_slow'].append(
					(ema_slow, {"above":boolean})
				)

	conditions = []

	# Form the open conditions 
	unique_ta_combos = all_subsets(open_ta_possibilities)
	for unique_ta_combo in list(unique_ta_combos):
		if not unique_ta_combo:
			continue
		unique_ta_combo = list(unique_ta_combo)

		# Recursion is your friend here, think of it as a map
		def recursive_form_map(combos_left, conditons_list_input, buy_bool):
			if len(combos_left) == 0:
				return Condition(
					conditions=conditons_list_input,
					buy=buy_bool
					)
			rec_conditions = []

			ta = combos_left.pop()
			for ta_alternates in all_strat_variations[ta.__qualname__]:
				conditons_list_input.append(ta_alternates)
				rec_conditions.append(
					recursive_form_map(
						combos_left,
						conditons_list_input,
						buy_bool
					)
				)
			return rec_conditions

		conditions += recursive_form_map(copy(unique_ta_combo), [], True)
		conditions += recursive_form_map(copy(unique_ta_combo), [], False)


	print(conditions)


	# Form all of the RSI Trades
	# for x in range(10,90):
	# 	for y in range(10, 90):
	# 		strats.append(
	# 			Strategy("RSI Buy %i Sell %i"%(y, x), (rsi, rsi), open_args={"rsinum":x, 'lt':True, 'buy':False}, close_args={"rsinum":y, 'lt':False, 'buy':True})
	# 		)

	# open_condition = Condition(conditions=[
	# 	(rsi, {"rsinum":70, 'lt':True})
	# 	(ema_slow, {"above":False})
	# ], buy=True)


	open_condition = Condition(conditions={
		rsi : {"rsinum":70, 'lt':True},
		ema_slow: {"above":False}
	}, buy=True)
	close_condition = Condition(conditions={
		rsi : {"rsinum":30, 'lt':False, 'buy':True},
		ema_slow: {"above":True, 'buy':True}
	}, buy=False)

	# Form all of the strategies here
	strats_example = [
		Strategy("RSI and EMA Slow", open_condition, close_condition)
	]

	if TESTMODE:
		strats = strats_example
	else:
		strats = strats + strats_example

	return strats


def brute_force_technical_indicators(symbol):

	# Load datas
	df = pd.read_csv('data/%s.csv'%symbol, sep=',')

	# Clean NaN values
	df = dropna(df)


	# Add all ta features
	df = add_all_ta_features(
		df, open="Open", high="High", low="Low", close="Close", volume="Volume"
	)

	strats = form_strats()

	success_strategies = []

	# Cycle through buy_methods and check success rate
	if MULTICORE:
		with Pool(processes=CORS_NUM) as pool:
			success_strategies = [pool.apply(execute_strategy, (strat, df,)) for strat in strats]
	else:
		for strat in strats:
			if execute_strategy(strat, df):
				success_strategies.append(strat)


	sorted_success_strategies = sorted(success_strategies, key=lambda x: x.account.money, reverse=True)

	results_str = ""
	for strat in sorted_success_strategies:
		results_str += "Strategy %s generated a %0.2f%% return\n"% (strat.name, strat.percent_change)

	#open text file
	
	with open("results/brute/%s.txt" %symbol, "w+") as resultfile:
		resultfile.write(results_str)

	print()



if __name__ == '__main__': 
	main()
