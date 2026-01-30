#!/bin/bash

portfolio_file="sample.xlsx"
portfolio_path="./$portfolio_file"

if [ ! -f "$portfolio_path" ]; then
	echo -e "Error: $portfolio_path does not exist."
elif [ "$(lsof | grep "$portfolio_path")" != "" ]; then
	echo -e "Error: $portfolio_path is currently in use."
else
	echo "Updating $portfolio_path."
	echo "Do not open it in any other program before the update is over."
	quoteupdater "$portfolio_path"
	source $HOME/venv/bin/activate
	exec python3 quoteupdater.py "$portfolio_path"
fi
