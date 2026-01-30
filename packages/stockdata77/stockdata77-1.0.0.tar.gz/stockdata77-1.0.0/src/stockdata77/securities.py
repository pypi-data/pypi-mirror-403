"""
	This file is part of stockdata77 Python module.

	Copyright 2022 Dandelion Systems <dandelion.systems@gmail.com>

	stockdata77 is free software; you can redistribute it and/or modify
	it under the terms of the MIT License.

	stockdata77 is distributed in the hope that it will be useful, but
	WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
	See the MIT License for more details.

	SPDX-License-Identifier: MIT
"""

import os
from json import loads
import xml.etree.ElementTree as xmlet
from http.client import HTTPSConnection
from threading import Thread
from time import sleep

class Securities:
	"""
	Class Securities creates and maintains a dictionary of security tickers. 
	It is a	Python stock exchange API wrapper. Currently supported APIs 
	are FMP, ALPHA VANTAGE (AV) and MOEX / MOEXBONDS.

	Use key = Securities.append(...) to fill it. Once you have all the security 
	tickers you need, you can use Securities[key] to obtain information on these 
	financial instruments. Alternatively, call individual getXXXXXX(key) 
	methods to obtain the ticker components like the security name, price and 
	price change.
	"""

	# Valid API providers
	__sx_list = ("FMP", "AV", "MOEX", "MOEXBONDS")

	# Delimiter for __securities dictionary key, 
	# the format is "SYMBOL:API", e.g. "AAPL:FMP"
	__delimiter = ":"

	def __init__(self):
		self.__securities = {}
		"""
		__securities dictionary holds the following:
		__securities[key] = [
			Company_long_name:str, 
			Current_price:float, 
			Change_to_previous_close:float, 
			API_key: str]

		Current_price is stored in the currency of the security or as
		percentage of the face value for bonds.
		Change_to_previous_close is stored as a fraction of the price, 
		i.e. the change of 2% will be stored as 0.02
		"""

		self.__maintaining = False
		self.__daemon = None
		return

	def makeKey(self, symbol:str, api:str) -> str:
		return symbol + self.__delimiter + api

	def splitKey(self, key:str) -> list[str]:
		return key.split(self.__delimiter)

	def getCompanyName(self, key:str) -> str:
		return self[key][0]

	def getPrice(self, key:str) -> float:
		return self[key][1]

	def getPriceChng(self, key:str) -> float:
		return self[key][2]

	def getAPIKey(self, key:str) -> str:
		return self[key][3]

	def __getitem__(self, key:str):
		return self.__securities[key]

	def __iter__(self):
		self.__maxCount = len(self.__securities)
		self.__iterCount = 0
		self.__valuesList = list(self.__securities.items())
		return self

	def __next__(self):
		if self.__iterCount < self.__maxCount:
			self.__iterCount += 1
			return self.__valuesList[self.__iterCount-1]
		else:
			raise StopIteration

	def __str__(self):
		result =  "SYMBOL".ljust(20," ") + "NAME".ljust(20, " ") + "PRICE".ljust(9, " ") + "CHANGE".ljust(10, " ") + "API".ljust(10, " ") + os.linesep
		result +=       "".ljust(19,"-") +    " ".ljust(20, "-") +     " ".ljust(9, "-") +      " ".ljust(10, "-") +   " ".ljust(10, "-") + os.linesep

		for key in self.__securities.keys():
			truncatedKey = key.split(self.__delimiter)[0]
			if len(truncatedKey) > 19: truncatedKey = truncatedKey[:16] + "..."
			truncatedName = self.getCompanyName(key)
			if len(truncatedName) > 19: truncatedName = truncatedName[:16] + "..."
			truncatedAPI = API = key.split(self.__delimiter)[1]
			if len(truncatedAPI) > 9: truncatedAPI = truncatedAPI[:6] + "..."

			result += truncatedKey.ljust(20," ") + truncatedName.ljust(20, " ") 
			if API == "MOEXBONDS":
				result += "{0:7.2f}% {1:8.2f}% ".format(100*self.getPrice(key), 100*self.getPriceChng(key))
			else:
				result += "{0:8.2f} {1:8.2f}% ".format(self.getPrice(key), 100*self.getPriceChng(key))
			result += truncatedAPI.ljust(8," ") + os.linesep
		
		return result

	def __contains__(self, key:str) -> bool:
		return key in self.__securities
	
	@staticmethod
	def __SE_API(symbol:str, api:str, api_key:str = "") -> list:
		"""
		Internal wrapper for stock exchange API calls.

		Should an error occur, depending on its nature either 
		an exception is thrown or [None, None, None] is returned.

		The following exceptions will be thrown:
		
		`socket.***` - in case of networking errors,
		
		`JSONDecodeError` - in case API returns a JSON object that 
		cannot be decoded like in the case of non-existent symbol; 
		should an XML-based API be used, this method silently returns
		if it cannot retreive the necessary
		"""
		def request(address:str, query:str) -> str:
			conn = HTTPSConnection(address)
			conn.request("GET", query)
			res = conn.getresponse()
			return res.read().decode('utf-8')
		
		company = None
		price = None
		changePercent = None

		match api:
			case "FMP":
				# Financial Modeling Prep:
				# API sample:
				# https://financialmodelingprep.com/stable/quote?symbol=AAPL&apikey=YOUR_API_KEY_HERE
				res = request(
					"financialmodelingprep.com", 
					"/stable/quote?symbol=" + symbol + "&apikey=" + api_key)

				json_obj = loads(res)
				json_result = json_obj[0]
				if json_result is not None:
					company = json_result['name']
					price = float(json_result['price'])
					changePercent = float(json_result['changePercentage']) / 100

			case "AV":
				# Alpha Vantage:
				# API sample:
				# https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_API_KEY_HERE
				res = request(
					"www.alphavantage.co", 
					"/query?function=GLOBAL_QUOTE&symbol=" + symbol + "&apikey=" + api_key)

				json_obj = loads(res)
				json_result = json_obj['Global Quote']
				if json_result is not None:
					company = json_result['01. symbol']
					price = float(json_result['05. price'])
					changePercent = float(json_result['10. change percent'][:-1]) / 100
		
			case "MOEX":
				# Shares and ETFs traded on MOEX
				# API sample:
				# https://iss.moex.com/iss/engines/stock/markets/shares/securities/X5.xml
				api_key = "" # discard API key for MOEX
				xml_result_str = request(
					"iss.moex.com", 
					"/iss/engines/stock/markets/shares/securities/" + symbol + ".xml")
				xml_result_tree = xmlet.fromstring(xml_result_str)

				for dta in xml_result_tree.findall("data"):
					if dta.attrib["id"] == "securities":
						for entry in dta.find("rows").findall("row"):
							if entry.attrib["BOARDID"] in ("TQBR", "TQTF"):
								company = entry.attrib["SECNAME"]
								break
					if dta.attrib["id"] == "marketdata":
						for entry in dta.find("rows").findall("row"):
							if entry.attrib["BOARDID"] in ("TQBR", "TQTF"):
								api_price = entry.attrib["MARKETPRICE"] if entry.attrib["LAST"] == "" else entry.attrib["LAST"]
								price = float(api_price)
								changePercent = float(entry.attrib["LASTTOPREVPRICE"]) / 100.00
								break
		
			case "MOEXBONDS":
				# Corporate and state bonds traded on MOEX
				# API samples:
				# https://iss.moex.com/iss/engines/stock/markets/bonds/securities/SU26248RMFS3.xml
				# https://iss.moex.com/iss/engines/stock/markets/bonds/securities/RU000A106LL5.xml
				api_key = "" # discard API key for MOEXBONDS
				xml_result_str = request(
					"iss.moex.com", 
					"/iss/engines/stock/markets/bonds/securities/" + symbol + ".xml")
				xml_result_tree = xmlet.fromstring(xml_result_str)

				for dta in xml_result_tree.findall("data"):
					if dta.attrib["id"] == "securities":
						for entry in dta.find("rows").findall("row"):
							if entry.attrib["BOARDID"] in ("TQCB", "TQOB"):
								company = entry.attrib["SECNAME"]
								price = float(entry.attrib["PREVPRICE"]) / 100.0 # previous day's close
								break
					if dta.attrib["id"] == "marketdata":
						for entry in dta.find("rows").findall("row"):
							if entry.attrib["BOARDID"] in ("TQCB", "TQOB"):
								if entry.attrib["LAST"] != "":                   # this will be empty on a non traiding day, in which case
									price = float(entry.attrib["LAST"]) / 100.00 # we have `price` assigned to previous day's close
								changePercent = float(entry.attrib["LASTTOPREVPRICE"]) / 100.00
								break
		
		return [company, price, changePercent]

	def append(self, symbol:str, api:str, api_key:str = "", force_update = False) -> (str | None):
		"""
		append() appends the dictionary __securities with the current 
		quote for the symbol. 

		symbol must be a valid symbol like "AAPL".
		api must be one of __sx_list[] values.
		
		The information is appended only in case __securities[] does not 
		yet have an entry with the same key. Otherwise, it is neither 
		appended nor updated, which allows to skip web API calls. 
		To force the update set force_update to True.

		The returned value is the key to the corresponding record in 
		__securities[]. If the key is not stored in the calling code it	can 
		be constructed again by calling the makeKey() menthod.
		"""
		
		if symbol is None: symbol = ""
		symbol = symbol.upper()
		if api is None: api = ""
		api = api.upper()
		if api_key is None: api_key = ""

		if symbol == "" or api not in self.__sx_list:
			return None

		key = self.makeKey(symbol, api)

		if key in self.__securities and not force_update:
			return key

		[company, price, changePercent] = self.__SE_API(symbol=symbol, api=api, api_key=api_key)
		
		if changePercent is not None:
			self.__securities[key] = [company, price, changePercent, api_key]
			return key
		
		return None
		
	def update(self, symbol:str, api:str, api_key:str = "") -> (str | None):
		"""
		update() appends or updates __securities[] with 
		the current quote for the symbol. 

		symbol must a valid security symbol like "AAPL".
		api must be one of __sx_list[] values.
		
		If __securities[] does not yet have an entry with the same key 
		it is appended. Otherwise, it is updated.

		The returned value is the key to the __securities dictionary 
		under which the	information is stored. If the key is not stored 
		in the calling code it can be constructed again by calling makeKey().
		"""

		return self.append(symbol=symbol, api=api, api_key=api_key, force_update=True)

	def remove(self, symbol:str, api:str) -> None:
		"""
		remove() removes the quote for the symbol. 

		symbol must a valid security symbol like "AAPL".
		api must be one of __sx_list[] values.
		
		If there is no entry for the symbol/api pair in the 
		database, remove() returns silently.
		"""
		key = self.makeKey(symbol, api)
		if key in self.__securities:
			del self.__securities[key]

	def __updateWorker(self, interval:int) -> None:
		while self.__maintaining:
			sleep(interval)
			for key in self.__securities.keys():
				(symbol, api) = self.splitKey(key)
				api_key = self.getAPIKey(key)
				self.update(symbol=symbol, api=api, api_key=api_key)

	def maintain(self, interval:int) -> None:
		"""
		Start updating quotes at regular intervals (in seconds).
		This is like having a stock exchange ticker for all security 
		symbols	in the __securities dictionary.
		Use desist() to stop.
		"""
		if not self.__maintaining:
			self.__maintaining = True
			self.__daemon = Thread(target=self.__updateWorker, args=(interval,), daemon=True)
			self.__daemon.start()

	def desist(self) -> None:
		"""
		Stop our stock exchange ticker.
		"""
		self.__maintaining = False

