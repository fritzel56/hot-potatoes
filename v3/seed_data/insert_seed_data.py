"""Writes CSVs from YF to BQ table. Assumes manually downloaded files.
2 per financial instrument. One using 'Historical Prices'. This gives
no dividend data when manually downloaded. One using 'Dividends Only'.
"""
import os
import glob
import pandas as pd
from google.cloud import bigquery


def process_file(file_name, ticker_name):
    """Takes in a csv and processes it for writing to GBQ

    Args:
        file_name (str): the name of the csv to be processed
        ticker_name (str): the name of the ticker the CSV contains info on

    Returns:
        df: properly formatted df for writing to GBQ
    """
    df = pd.read_csv(file_name)
    df['Date'] = pd.to_datetime(df.Date, infer_datetime_format=True)
    df.insert(0, 'Ticker', ticker_name)
    return df


def write_to_gbq(data, client, table):
    """Takes in a dataframe and writes the values to GBQ

    Args:
        data (df): the dataframe to be written
        client (Client): GBQ client
        table (GBQ Table): GBQ table reference
    """
    rows_to_insert = data.values.tolist()
    # write data
    errors = client.insert_rows(table, rows_to_insert)
    assert errors == []


def name_extractor(file_name):
    """Takes in a filename and extracts the ticker embedded in it

    Args:
        file_name (str): the name of the csv file to extract from

    Returns:
        str: the ticker name for which the file holds data
    """
    splitter = '.'
    locs = [pos for pos, char in enumerate(file_name) if char == splitter]
    ticker_name = file_name[:locs[1]]
    return ticker_name


if __name__ == '__main__':
    # setup connection variables for GBQ
    project = os.environ['PROJECT']
    dataset = os.environ['DATASET']
    price_tablename = os.environ['PRICE_TABLENAME']
    dividend_tablename = os.environ['DIVIDEND_TABLENAME']
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset)
    price_table_ref = bigquery.TableReference(dataset_ref, price_tablename)
    price_table = client.get_table(price_table_ref)
    div_table_ref = bigquery.TableReference(dataset_ref, dividend_tablename)
    div_table = client.get_table(div_table_ref)

    # pull all csvs in local folder and process list
    csvs = [f for f in glob.glob("*.csv")]
    csvs = sorted(csvs, key=str.casefold)
    tickers = set(name_extractor(name) for name in csvs)
    ticker_map = {}
    for ticker in tickers:
        ticker_map[ticker] = [csv for csv in csvs if ticker in csv]

    # process and upload data for each ticker
    for key in ticker_map.keys():
        price_data = process_file(ticker_map[key][0], key)
        write_to_gbq(price_data, client, price_table)
        if len(ticker_map[key]) == 2:
            dividend_data = process_file(ticker_map[key][1], key)
            write_to_gbq(dividend_data, client, div_table)
