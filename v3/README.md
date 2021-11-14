# V3

V2 ran well but you had to wait until mid-month which is when Yahoo updated their total 1 year return numbers. I wanted to be able to send something out on the first business day. This code does this. It also somewhat improves the error reporting.

Update: At some point in 2021, Yahoo changed their website layout which broke my webscraper. Instead of fixing, I decided to move to using yfinance which is a python package which pulls the data nicely for us.

Main cons to this approaoch:
1) some manual work needed to do a one time load of historical data
2) calculated 1 year total returns do not align exactly with Yahoo's values

## File Overview
| File | Description |
|------|-------------|
| seed_data | Folder contains code used to load one time historical data. |
|  close_value.sql | SQL to pull the close value for a ticker at a specific date. |
| divs.sql | SQL to pull total dividend payouts for a ticker between two dates. |
| main.py | Main code used to collect data and send email. |
| max_date_where.sql | SQL to find the most recent date before a specific date for which we have price data for a specific ticker. |
| merge_divs.sql | SQL used to load new data from the dividend staging table into the dividend base table. |
| merge_price.sql | SQL used to load new data from the price staging table into the price base table. |
| min_max_date.sql | SQL which finds the max dates for all tickers in the price table and returns the oldest one. |
| requirements.txt | Packages needed to run the code. |
| stocks.yaml | YAML file containing info on stocks to be checked. Edit this file to track your stocks of interest. |

To run this, two new tables need to be created (see `seed_data`). Then follow the same setup instructions outlined in the V2 README.

You will also need to add the following environment variables on top of what you already had for v2:

| Variable Name | Variable Definition |
|---------------|---------------------|
| PROJECT_ID | Name of the Google Cloud project associated with the BigQuery datasets. |
| PRICE_TABLENAME | Name of the table where the price data is stored. |
| DIVIDEND_TABLENAME | Name of the table where the dividend data is stored. |

To customize which stocks you track, you should only have to edit the `stocks.yaml` file and load the historical data as detailed in `seed_data`.
