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
    df['Ticker'] = ticker
    return df


def get_bq_data():
    """Queries BQ for the most recent entry for each ETF
    Returns:
        df: The most recent recorded returns for each ETF
    """
    project_id = os.environ['PROJECT_ID']
    dataset = os.environ['DATASET']
    tablename = os.environ['TABLENAME']
    with open('query_monthly_data.sql') as f:
        query = f.read()
    query = query.format('`'+project_id+'.'+dataset+'.'+tablename+'`')
    client = bigquery.Client()
    return client.query(query).result().to_dataframe()


def write_to_gbq(ticker, data, most_recent):
    """Takes in a dataframe and writes the values to BQ
    Args:
        stocks_df(df): the dataframe to be written
    """
    latest = most_recent.loc[most_recent.ticker==ticker, 'snap_date']
    if len(latest)==0:
        to_write = data
    else:
        to_write = data.loc[data.Date2>latest[0]]
    dataset = os.environ['DATASET']
    tablename = os.environ['TABLENAME']
    # set up connection details
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset)
    table_ref = bigquery.TableReference(dataset_ref, tablename)
    table = client.get_table(table_ref)
    # convert to list of lists
    rows_to_insert = to_write.values.tolist()
    # write data
    errors = client.insert_rows(table, rows_to_insert)
    assert errors == []


def id_new_data():
    """Queries BQ for the most recent entry for each ETF
    Returns:
        old_df: the
    """

def error_composition(e):
    """Composes an email in the event of an exception with exception details.
    Args:
        e(Exception): the exception which was raised
    Returns:
        dict: data structure containing the composed email ready for MJ's API
    """
    contact_email = os.environ['contact_email']
    contact_name = os.environ['contact_name']
    data = {
      'Messages': [
        {
          "From": {
            "Email": contact_email,
            "Name": contact_name
          },
          "To": [
            {
              "Email": contact_email,
              "Name": contact_name
            }
          ],
          "Subject": "There was an error with the hot potatoes run",
          "HTMLPart": "There was an error with the hot potatoes run: {}".format(' '.join(e.args)),
        }
      ]
    }
    return data


def send_email(email):
    """Takes in a composed email and sends it using the mailjet api
    Args:
        email(dict): dict containing all relevant fields needed by the mailjet API
    """
    api_key = os.environ['api_key']
    api_secret = os.environ['api_secret']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    result = mailjet.send.create(data=email)


def kickoff(request):
    """Function which orchestrates the rest of the code
    Args:
        request: passed as part of the Google Function orchestration service. Not used.
    """
    with open('stocks.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    # tickers for which we want reports
    tickers = data['tickers']
    # dictionary connecting tickers to readible names. Used in email.
    name_mapping = data['mapping']
    try:
        most_recent = get_bq_data()
        for ticker in tickers:
            data = get_daily_data(ticker)
            write_to_gbq(ticker, data, most_recent)
    except Exception as e:
        email = error_composition(e)
        send_email(email)



        pct_df = pd.DataFrame(list(pct.items()), columns=['etf', 'return'])
        if not stock_change(pct_df):
            email = compose_summary_email(pct, name_mapping)
            send_email(email)
        pct_df = prep_data(pct_df)
        write_to_gbq(pct_df)
    except Exception as e:
        email = error_composition(e)
        send_email(email)
