# Python wrapper for stock exchange API providers

`stockdata77` module provides `Securities` class to simplify interfacing with stock exchnage API providers. It currently supports APIs of Financial Modeling Prep, Alpha Vantage and MOEX. It is designed primarily to be used with shares, bonds and ETF symbols.

Please note that FMP and AV providers will require an API key. Also note that Yahoo Finance API support has been discontinued since version 0.0.5 as the provider has shut down its API.

## Usage summary

`Securities` class creates and maintains a dictionary of  securities quotes. Stored values are security long name, current price and change to previous close. The price is stored in the currency of the security. The change is a fraction of the price, i.e. a change of 2% will be stored as 0.02.

Use `append(symbol, api, api_key)` method to fill it with individual stock quotes. 

Once you have all the quotes you need, you can use `Securities[key]` to obtain trading data as a list of values. Alternatively, call individual `getXXXXXX()` methods to obtain various components of the list. Prior to calling any of these you can use the `in` operator to check if a `key` has a corresponding record.

The `key` is composed out of the stock symbol and the name of the API provider. `makeKey(symbol, api)` will 
get you the `key`. Or you can simply store the value returned by `append()` or `update()`. Use `splitKey()` to reverse `makeKey()`.

The instances of the `Securities` class are iterable. Trying this code

	import stockdata77

	stocks = Securities()
	stocks.append(symbol="TSLA", api="AV", api_key="YOUR_API_KEY_HERE")
	stocks.append(symbol="NVDA", api="AV", api_key="YOUR_API_KEY_HERE")
	for entry in stocks:
		print(entry)

will print tuples of `(key, [name, price, change])` like this:

	('TSLA:AV', ['TSLA', 417.78, 0.068245, 'YOUR_API_KEY_HERE'])
	('NVDA:AV', ['NVDA', 182.55, 0.020516999999999997, 'YOUR_API_KEY_HERE'])

Attempting to cast the whole instance to `str` type will get you a formatted table with the current quotes. For instance appending 

	print(stocks)

to the example above will get you this:

	SYMBOL              NAME                PRICE    CHANGE    API       
	------------------- ------------------- -------- --------- ---------
	TSLA                TSLA                  417.78     6.82% AV      
	NVDA                NVDA                  182.55     2.05% AV 

Company NAME in the examples above is not a long name but the same as the stock symbol beacause of the API provider used. Other providers like FMP and MOEX will give full company names.

Use `maintain(interval)` to fork a thread that updates the quotes at the given intervals in seconds. Invoking `desist()` will stop the updates. See the included `simple_demo.py` script for an example.

## Demo code

See the included `samples\simple_demo.py` for a very simple demo.

The other script in the `samples` folder privides a more comprehensive example. It reads and updates an Excel file with prices and price changes for various shares, ETFs and bonds.

## `Securities` class methods

> `Securities` class does not expose any fields. Use the methods described below to obtain the necessary. In addition to these you can iterate through an instance of `Securities`, read individual records by indexing it with a `key` (see `append()` for the explanation of keys), and cast it to `str` type which returns a formatted text table with full stored data primarily for debugging purposes.

`append(symbol:str, api:str, api_key:str = "", forceUpdate = False)` - appends the internal dictionary with the current trading data for the `symbol`. How close it is to real-time depends on the API provider and, in case you supply `api_key`, on your subscription plan. `symbol` must be a valid symbol like "AAPL", `api` must be one of "FMP, "AV", "MOEX" or "MOEXBONDS". The information is appended only in case the internal dictionary does not yet have an entry with the same key. Otherwise, it is neither appended nor updated, which allows skipping web API calls. To force the update set `forceUpdate` to `True`. It is mandatory to provide `api_key` if either "FMP" or "AV" is used.

Using `append()` is the way to fill the `Securities` instance initially. The symbols can come from a source that might contain duplicates and sticking with `forceUpdate = False` and thus skiping web API calls for duplicate symbols will optimise your code for speed and minimise the impact on the API providers.

The returned value is the `key` to the the internal dictionary for the record of this symbol/api pair. If the returned `key` is not stored in the calling code it can be constructed again by calling the `makeKey()` menthod. If either the supplied `symbol` or the `api` names are invalid, `append()` returns `None`.

`update(symbol:str, api:str, api_key:str = "")` - same as `append()` but with `forceUpdate` set to `True`.

`remove(symbol:str, api:str)` - removes the quote for the `symbol`. The supplied `symbol` and `api` are the same as when calling `append()`. If there is no entry for the symbol/api pair in the internal database, `remove()` returns silently.

`maintain(interval:int)` - start updating stock quotes at regular intervals (in seconds). This method forks a thread that keeps calling the relevant APIs and updating the internal dictionary with new data. Use `desist()` to stop. Mind that your API provider may impose limits on the number of calls per a period of time. Such quotas will usually depend on your subscription plan, so make sure you do not exhaust it while debugging.

`desist()` - stop updating stock quotes.

`makeKey(symbol:str, api:str)` - makes a `key` used in the internal dictionary maintained by `Securities` to index the trading data records. Returns a `str` value of the `key`.

`splitKey(key:str)` - reverses `makeKey()` and returns a tuple of `(symbol, api)`.

`getCompanyName(key:str)` - obtains a long company name for the symbol used to make the `key`.

`getPrice(key:str)` - obtains a `float` value of the last known price for the symbol used to make the `key`.

`getPriceChng(key:str)` - obtains  a `float` value of the last known price change from previous close for the symbol used to make the `key`. The change is stored as a fraction of the price, i.e. a change of 2% will be stored as 0.02.

`getAPIKey(key:str)` - obtains  a `str` value of the API key used to obtain the security's parameters.

## Final notes

### Usage scenarios

> Note: The examples below use "AV" simply to avoid using a specific `api_key` paramater as AV API works without errors with just something like "YOUR_API_KEY_HERE" for demo purposes.

There are at least two scenarios the `Securities` class was designed for.

#### Static
Add quotes with `append()` and then use them without updating. Sample code:
	
	#!/usr/bin/env python3

	from stockdata77 import Securities

	shares = Securities()
	key = stocks.append("AAPL", "AV", "YOUR_API_KEY_HERE")

	if key is not None:
		print("Stock quote for AAPL")
		print("Name   = " + shares.getCompanyName(key))
		print("Price  = {0:.2f}".format(shares.getPrice(key)))
		print("Change = {0:.2f}%".format(shares.getPriceChng(key)*100))
	else:
		print("Quote not found")

#### Dynamic
Add quotes with `append()` and then keep them alive to use in some dymnamic way like plotting real-time price graphs or directing business logic. The API provider and your subscription plan should allow real-time quotes of course. Sample code:

	#!/usr/bin/env python3
	
	from time import sleep
	from stockdata77 import Securities

	shares = Securities()
	shares.append("AAPL", "AV", "YOUR_API_KEY_HERE")

	print(shares)

	shares.maintain(2) # start updating the quotes at 2 second intervals

	for i in range(4):
		sleep(2)       # wait for updates
		print(shares)  # display updated quotes

	shares.desist()    # stop updating the quotes

### Thread safety

Avoid `remove()`-ing in more than one thread at a time. If you `maintain()` and you need to `remove()` a quote, call `desist()` first to pause the updates, then call `remove()` and invoke `maintain()` again.
