import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna

global_starting_money = 10000

class Strategy:

	def __init__(self, 
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
			print("Closed %i shares at price %f"%(self.holdnum, price))
			self.holdnum = 0
		# Else start long
		else:
			buyammount = int((self.money*risknum)/price)
			self.money -= (price*buyammount)
			self.holdnum = buyammount
			print("Bought %i shares at price %f"%(buyammount, price))

		print("Money: %f"%self.money)

	def sell(self, price, risknum=0):
		risknum = self.risknum if risknum==0 else .2
		# If short already do nothing
		if self.holdnum < 0:
			return
		# If long, close
		elif self.holdnum > 0:
			self.money += (price*self.holdnum)
			print("Closed %i shares at price %f"%(self.holdnum, price))
			self.holdnum = 0
		# Else start short
		else:
			buyammount = int(((self.money*risknum)/price))
			self.money += (price*buyammount)
			self.holdnum = buyammount*-1
			print("Sold %i shares at price %f"%(buyammount, price))

		print("Money: %f"%self.money)


# Needs arg 
# rsinum
# lt TRUE or FALSE
def rsi(row, i, args={}, **kwargs):
	if args['lt']:
		if row['momentum_rsi'] <= args["rsinum"]:
			print("RSI Value: %f" %row['momentum_rsi']) 
			return True
	else:
		if row['momentum_rsi'] >= args["rsinum"]:
			print("RSI Value: %f" %row['momentum_rsi']) 
			return True


# def rsilow(row, i, rsinum=30, args={}, **kwargs):
# 	# if int(df.at[i, 'momentum_rsi']) > rsinum:
# 	# 	return True
# 	if row['momentum_rsi'] < rsinum:
# 		print("RSI Value: %f" %row['momentum_rsi']) 
# 		return True

# Combo one buy method with one sell method?

def main():
	# Load datas
	df = pd.read_csv('SPY.csv', sep=',')

	# Clean NaN values
	df = dropna(df)

	# Add all ta features
	df = add_all_ta_features(
		df, open="Open", high="High", low="Low", close="Close", volume="Volume"
	)

	# Form all of the strategies here
	strats = [
		Strategy((rsi, rsi), open_args={"rsinum":70, 'lt':True, 'buy':False}, close_args={"rsinum":60, 'lt':False, 'buy':True})
	]

	# Cycle through buy_methods and check success rate
	lastrow = None
	for i, row in df.iterrows():
		for strat in strats:
			strat.act(i, row)
		lastrow = row

	for strat in strats:
		# Close the account first
		if strat.account.holdnum > 0:
			strat.account.sell(lastrow['Close'])
		elif strat.account.holdnum < 0:
			strat.account.buy(lastrow['Close'])
		print("Account Money: %f"%strat.account.money)
		percent_change = (strat.account.money/global_starting_money - 1)*100
		print("This strategy generated a %0.2f%% return"% percent_change)

	# Final step is to close all account positions, or just report the total


main()
