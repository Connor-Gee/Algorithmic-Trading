import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math
from secrets import IEX_CLOUD_API_TOKEN



# Batch calls are limited to 100 tickers per call. S&P 500 split using:
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


stocks = pd.read_csv("sp_500_stocks.csv")
my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy']
final_dataframe = pd.DataFrame(columns = my_columns)

# Create batches
symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

# Retrieve data for each ticker in batches, re-combine the batches and append the series to the dataframe
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
        pd.Series(
            [
                symbol,
                data[symbol]['quote']['latestPrice'],
                data[symbol]['quote']['marketCap'],
                'N/A'
            ],

            index = my_columns
        ),
        
        ignore_index=True
)

# Retrieve user portfolio size
portfolio_size = input("Enter portfolio size (USD): ")
try:
    val = float(portfolio_size)
except:
    print("Enter integer value")
    portfolio_size = input("Enter portfolio size (USD): ")
    val = float(portfolio_size)

# Determine position size and number of shares to buy
position_size = val/len(final_dataframe.index)
for i in range(0, len(final_dataframe.index)):
    final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])
    

# Write to Excel file
writer = pd.ExcelWriter('recommended trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, 'Recommended Trades', index=False)
background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

dollar_format = writer.book.add_format(
        {
            'num_format':'$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

integer_format = writer.book.add_format(
        {
            'num_format':'0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
column_formats = { 
                    'A': ['Ticker', string_format],
                    'B': ['Price', dollar_format],
                    'C': ['Market Capitalization', dollar_format],
                    'D': ['Number of Shares to Buy', integer_format]
                    }

for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Recommended Trades'].write(f'{column}1', column_formats[column][0], string_format)
writer.save()
