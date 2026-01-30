# This is a demo code for Stocks class implemented
# in stockquotes module
#
# Copyright 2022 Dandelion Systems <dandelion.systems@gmail.com>
#
# SPDX-License-Identifier: MIT

from time import sleep
from stockdata77 import Securities

shares = Securities() # create a database of stock quotes and fill it up
shares.append("AAPL", "AV", "YOUR_API_KEY_HERE")
shares.append("U", "AV", "YOUR_API_KEY_HERE")
shares.append("HEAD", "MOEX")

print(shares)

shares.maintain(2) # start updating the quotes at 2 second intervals

for i in range(4):
	sleep(2)       # wait for updates
	print(shares)  # display updated quotes

shares.desist()    # stop updating the quotes

