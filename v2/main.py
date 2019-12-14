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


def prep_data(stocks_df):
    """Takes in a df and formats in to be written to BQ
    Args:
        stocks_df(df): the current data
    Returns:
        df: df properly formatted to be written to BQ
    """
    # add timestamp
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stocks_df['current_time'] = current_time
    # change column order
    cols = ['etf', 'current_time', 'return']
    stocks_df = stocks_df[cols]
    return stocks_df


def write_to_gbq(stocks_df):
    """Takes in a dataframe and writes the values to BQ
    Args:
        stocks_df(df): the dataframe to be written
    """
    dataset = os.environ['DATASET']
    tablename = os.environ['TABLENAME']
    # set up connection details
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset)
    table_ref = bigquery.TableReference(dataset_ref, tablename)
    table = client.get_table(table_ref)
    # convert to list of lists
    rows_to_insert = stocks_df.values.tolist()
    # write data
    errors = client.insert_rows(table, rows_to_insert)
    assert errors == []


def stock_change(pct_df):
    """Takes in a the most recent data, pulls in the most recent data in BQ,
       and sees if they're the same.
    Args:
        pct_df(df): the current data
    Returns:
        bool: True if the current data is equal to the most recent data. Otherwise False.
    """
    df_hist = get_bq_data()
    overlap = df_hist.etf.isin(pct_df.etf.to_list())
    right = pct_df.set_index('etf').sort_index()
    left = df_hist.loc[overlap].set_index('etf').sort_index()
    return left.equals(right)


def get_url(ticker):
    """Takes in a stock ticker and returns the relevant Yahoo Finance link.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        str: the Yahoo Finance URL of the supplied ticker
    """
    url = 'https://finance.yahoo.com/quote/{}/performance?p={}'.format(ticker, ticker)
    return url


def get_yearly_return(ticker):
    """Takes in a stock ticker and returns the 1-year total return.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        float: the total 1-year return for the ticker
    """
    url = get_url(ticker)
    content = urllib2.urlopen(url).read().decode('utf-8')
    starting = content.find('trailingReturns')+17
    end = content.find("}}", starting)+2
    tree = content[starting:end]
    jsonList = json.loads(tree)
    return jsonList['oneYear']['raw']


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


def compose_summary_email(pct, name_mapping):
    """Composes an email whose subject lists the highest performing stock
       and which includes a table showing all stock performance.
    Args:
        pct(dict): maps between stock tickers and 1-year total returns
        name_mapping(dict): maps between stock tickers and their definitions
    Returns:
        dict: data structure containing the composed email ready for MJ's API
    """
    pct_nice_name = {}
    for key in pct.keys():
        pct_nice_name[key[:-3]] = pct[key]
    highest_return_ticker = max(pct_nice_name, key=pct_nice_name.get)
    highest_return = pct_nice_name[highest_return_ticker]
    df_pct = pd.DataFrame(data=pct_nice_name, index=['YTD'])
    df_name = pd.DataFrame(data=name_mapping, index=['Desc'])
    df_tot = df_pct.transpose().merge(right=df_name.transpose(), left_index=True, right_index=True)
    df_tot = df_tot.sort_values(by='YTD', ascending=False).transpose()
    summary_table = df_tot.to_html()
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
          "Subject": "{} has the highest returns".format(highest_return_ticker),
          "HTMLPart": "<h3>Today's leader is {} at {}.</h3><br />Summary:<br />{}".format(highest_return_ticker, highest_return, summary_table),
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
    pct = {}
    try:
        for ticker in tickers:
            pct[ticker] = get_yearly_return(ticker)
        pct_df = pd.DataFrame(list(pct.items()), columns=['etf', 'return'])
        if not stock_change(pct_df):
            email = compose_summary_email(pct, name_mapping)
            send_email(email)
        pct_df = prep_data(pct_df)
        write_to_gbq(pct_df)
    except Exception as e:
        email = error_composition(e)
        send_email(email)
