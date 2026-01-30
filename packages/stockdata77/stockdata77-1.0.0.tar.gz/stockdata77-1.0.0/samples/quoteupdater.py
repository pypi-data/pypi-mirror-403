import sys
import os
from optparse import OptionParser

from openpyxl import load_workbook
from stockdata77 import Securities
from time import sleep

def main():
	optParser = OptionParser(usage="Usage: %prog [options] file_with_stock_tickers.xlsx" + os.linesep + "See --help for options.")
	optParser.add_option("-d", "--dry", help="only simulate, don't update the file", action="store_true", dest='dry')

	try:
		(options,args) = optParser.parse_args(sys.argv)
		dry = options.dry
		workbookName = args[1]
	except IndexError:				# handle unknown options as OptionParser does not
		optParser.print_help()		# print help by default in this case
		return
	except:							# if --help is specified, OptionParser prints help by defaut
		return						# and throws an exception. We handle it gracefully here

	workbook = load_workbook(workbookName)

	sheetsToUpdate = {}

	try:
		ctrlSheet = workbook["#Ctrl"]
		i = 1
		while (sheetName := ctrlSheet["A" + str(i)].value):
			if sheetName == "#end of list":
				break 

			symbols_str = str(ctrlSheet["B" + str(i)].value)
			_symbols = symbols_str.split(":")

			names_str = str(ctrlSheet["C" + str(i)].value)
			_names = names_str.split(":")

			prices_str = str(ctrlSheet["D" + str(i)].value)
			_prices = prices_str.split(":")

			changes_str = str(ctrlSheet["E" + str(i)].value)
			_changes = changes_str.split(":")

			apis_str = str(ctrlSheet["F" + str(i)].value)
			_apis = apis_str.split(":")

			keys_str = str(ctrlSheet["G" + str(i)].value)
			_keys = keys_str.split(":") if ":" in keys_str else None

			sheetsToUpdate[sheetName] = [_symbols, _names, _prices, _changes, _apis, _keys]

			i += 1
	except:
		print("Error: the workbook must have a properly formatted #Ctrl sheet.")
		return

	securities = Securities()

	for sheetName in sheetsToUpdate:
		if not dry:
			print("Updating sheet " + sheetName + ".")

		sheet = workbook[sheetName]

		_symbols = sheetsToUpdate[sheetName][0]
		symbols = sheet[_symbols[0]:_symbols[1]]

		_names = sheetsToUpdate[sheetName][1]
		names = sheet[_names[0]:_names[1]]
		
		_prices = sheetsToUpdate[sheetName][2]
		prices = sheet[_prices[0]:_prices[1]]
		
		_changes = sheetsToUpdate[sheetName][3]
		changes = sheet[_changes[0]:_changes[1]]
		
		_apis = sheetsToUpdate[sheetName][4]
		apis = sheet[_apis[0]:_apis[1]]
		
		if not (_keys := sheetsToUpdate[sheetName][5]):
			keys = [None for x in symbols]
		else:
			keys = sheet[_keys[0]:_keys[1]]

		if not (
			len(symbols) == len(names) == len(prices) == 
			len(changes) == len(apis) == len(keys)):
			print(f"Error: ranges for `{sheetName}` are not equal.")
			return

		for _symbol, _name, _price, _change, _api, _key in \
			zip(symbols, names, prices, changes, apis, keys):   
			                       # sheet[] returns a tuple even if iterated, 
			symbol = _symbol[0]    # so we need [0] to get one cell
			name = _name[0]
			price = _price[0]
			change = _change[0]
			api = _api[0]
			if _key:
				key = _key[0]
				api_key = key.value
			else:
				api_key = ""
			
			if api.value == "AV":  # sleep between requests to free tier of AV API
				sleep(1.1)

			if (k := securities.append(symbol.value, api.value, api_key)) is not None and not dry:
				name.value = securities.getCompanyName(k) # update the company name
				price.value = securities.getPrice(k) 	  # update the current price
				change.value = securities.getPriceChng(k) # update the change

	if dry:
		print(securities)
	else:
		workbook.save(workbookName)

if __name__ == "__main__":
	try:
		main()
	except:
		print (sys.exc_info())
