"""Code used to track 1-year total returns to help enable a hot potato strategy.
"""
import urllib.request as urllib2
import json
from mailjet_rest import Client
import os
import pandas as pd
import yaml
from google.cloud import bigquery
import datetime


def get_url_daily(ticker):
    """Takes in a stock ticker and returns the relevant Yahoo Finance link.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        str: the Yahoo Finance URL of the supplied ticker
    """
    url='https://finance.yahoo.com/quote/{}/history?p={}'.format(ticker, ticker)
    return url


def get_daily_data(ticker):
    """Takes in a stock ticker and returns daily performance.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        df: roughly the last 99 days of performance
    """
    url = get_url_daily(ticker)
    content = urllib2.urlopen(url).read().decode('utf-8')
    starting = content.find('<table')
    end = content.find("</table", starting)
    table = content[starting:end]
    dfs = pd.read_html(table)
    df = dfs[0]
    # get rid of any dividend info
    dividend_rows = df.Open.str.contains('Dividend')
    df = df.loc[~dividend_rows]
    # get rid of the notes at the end
    df = df[0:len(df)-1]
    # make the columns numeric
    cols = df.columns.drop('Date')
    df[cols] = df[cols].apply(pd.to_numeric)
    df['Date2'] = pd.to_datetime(df.Date,infer_datetime_format=True)
    return df
