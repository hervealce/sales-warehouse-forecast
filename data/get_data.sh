#!/usr/bin/env bash
# Downloads UCI Online Retail II (CC BY 4.0) and converts both sheets to one CSV.
set -e; cd "$(dirname "$0")"
curl -L -o retail2.zip https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
unzip -o retail2.zip
python -c "import pandas as pd; pd.concat(pd.read_excel('online_retail_II.xlsx', sheet_name=None).values()).to_csv('retail.csv', index=False)"
