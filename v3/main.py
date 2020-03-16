"""Code used to track 1-year total returns to help enable a hot potato strategy.
"""
import urllib.request as urllib2
import sys
from mailjet_rest import Client
import os
import pandas as pd
import yaml
from google.cloud import bigquery
import datetime as dt
import traceback


def new_period_url(ticker, min_dt):
    """Takes in a stock ticker and returns the relevant Yahoo Finance link.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        str: the Yahoo Finance URL of the supplied ticker
    """
    start = yahoo_date_calc(min_dt)
    end = yahoo_date_calc(dt.datetime.today())
    url = 'https://finance.yahoo.com/quote/{}/history?period1={}&period2={}&interval=1d&filter=history&frequency=1d'.format(ticker, start, end)
    return url


def yahoo_date_calc(target_date):
    """Takes in a datetime date and converts it to Yahoo's date system
    Args:
        target_date(dt): datetime date
    Returns:
        int: the date number in Yahoo's date system
    """
    nov_30_2018 = 1543554000
    base_date = dt.datetime.strptime('2018-11-30', '%Y-%m-%d')
    days = (target_date - base_date).days
    y_date = nov_30_2018 + 86400 * days
    return y_date


def data_return(url, ticker):
    """Takes in a stock ticker and returns daily performance.
    Args:
        ticker(str): the ticker whose info we want
    Returns:
        df: roughly the last 99 days of performance
    """
    content = urllib2.urlopen(url).read().decode('utf-8')
    starting = content.find('<table')
    end = content.find("</table", starting)
    table = content[starting:end]
    dfs = pd.read_html(table)
    df = dfs[0]
    # get rid of any dividend info
    dividend_rows = df.Open.str.contains('Dividend')
    split_rows = df.Open.str.contains('Split')
    df_price = df.loc[(~dividend_rows) & (~split_rows)]
    # get rid of the notes at the end
    df_price = df_price[0:len(df_price)-1]
    # make the columns numeric
    cols = df_price.columns.drop(['Date', 'Close*'])
    # required field. want an error if it's missing
    df_price['Close*'] = df_price['Close*'].apply(pd.to_numeric)
    # not required fields. accept NaNs if not present
    df_price[cols] = df_price[cols].apply(pd.to_numeric, errors='coerce')
    df_price[cols] = df_price[cols].fillna(-9999)
    df_price['Date'] = pd.to_datetime(df_price.Date, infer_datetime_format=True)
    df_price.insert(0, 'Ticker', ticker)
    # format the dividend data
    df_div = df.loc[dividend_rows]
    if len(df_div)>0:
        df_div['div'] = df_div.Open.apply(lambda x: x.split(' ')[0])
        df_div = df_div[['Date', 'div']]
        cols = df_div.columns.drop('Date')
        df_div[cols] = df_div[cols].apply(pd.to_numeric)
        df_div['Date'] = pd.to_datetime(df_div.Date, infer_datetime_format=True)
        df_div.insert(0, 'Ticker', ticker)
    return (df_price, df_div)


def get_bq_data(sql, client):
    """Queries BQ for the most recent entry for each ETF
    Returns:
        df: The most recent recorded returns for each ETF
    """
    return client.query(sql).result().to_dataframe()


def write_to_gbq(data, client, table):
    """Takes in a dataframe and writes the values to BQ
    Args:
        stocks_df(df): the dataframe to be written
    """
    # convert to list of lists
    rows_to_insert = data.values.tolist()
    # write data
    errors = client.insert_rows(table, rows_to_insert)
    assert errors == []


def error_composition(e):
    """Composes an email in the event of an exception with exception details.
    Args:
        e(Exception): the exception which was raised
    Returns:
        dict: data structure containing the composed email ready for MJ's API
    """
    contact_email = os.environ['contact_email']
    contact_name = os.environ['contact_name']
    err = sys.exc_info()
    err_message = traceback.format_exception(*err)
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
          "HTMLPart": "There was an error with the hot potatoes run: {} ".format(err_message),
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
    df_pct = df_pct.round(2)
    df_name = pd.DataFrame(data=name_mapping, index=['Desc'])
    df_tot = df_pct.transpose().merge(right=df_name.transpose(),
                                      left_index=True, right_index=True)
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
          "HTMLPart": "<h3>Today's leader is {} at {}.</h3><br />Summary:<br />{}".format(highest_return_ticker, highest_return.round(2), summary_table),
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


def main_kickoff():
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
    # set up GBQ variables
    project_id = os.environ['PROJECT_ID']
    dataset = os.environ['DATASET']
    price_table_name = os.environ['PRICE_TABLENAME']
    div_table_name = os.environ['DIVIDEND_TABLENAME']
    # set up connection details
    client = bigquery.Client()
    dataset_ref = client.dataset(dataset)
    price_query_path = '`'+project_id+'.'+dataset+'.'+price_table_name+'`'
    div_query_path = '`'+project_id+'.'+dataset+'.'+div_table_name+'`'
    # get the references for the load tables
    load_price_table_name = 'load_'+price_table_name
    load_price_table_ref = bigquery.TableReference(dataset_ref,
                                                   load_price_table_name)
    load_price_table = client.get_table(load_price_table_ref)
    load_price_query_path = '`'+project_id+'.'+dataset+'.'+load_price_table_name+'`'
    load_div_table_name = 'load_'+div_table_name
    load_div_table_ref = bigquery.TableReference(dataset_ref,
                                                 load_div_table_name)
    load_div_table = client.get_table(load_div_table_ref)
    load_div_query_path = '`'+project_id+'.'+dataset+'.'+load_div_table_name+'`'
    # get max date in database
    with open('min_max_date.sql') as f:
        min_max_sql = f.read()
    min_max_sql = min_max_sql.format(price_query_path)
    max_dt = get_bq_data(min_max_sql, client)
    base_dt = max_dt['min_max_dt'].iloc[0]
    # if only have a one date range, return is weird so look at min 7 day range
    pull_dt = base_dt - dt.timedelta(days=14)
    # empty load tables
    sql = "delete FROM "+load_price_query_path+" where snap_date > '2000-01-01'"
    empty = get_bq_data(sql, client)
    sql = "delete FROM "+load_div_query_path+" where snap_date > '2000-01-01'"
    empty = get_bq_data(sql, client)
    # pull data for each ticker from Yahoo
    for ticker in tickers:
        url = new_period_url(ticker, pull_dt)
        (price_data, div_data) = data_return(url, ticker)
        # if there is new data, write it to the load tables
        if len(price_data) > 0:
            write_to_gbq(price_data, client, load_price_table)
            with open('merge_price.sql') as f:
                sql = f.read()
            sql = sql.format(price_query_path, load_price_query_path)
            empty = get_bq_data(sql, client)
        if len(div_data) > 0:
            write_to_gbq(div_data, client, load_div_table)
            with open('merge_divs.sql') as f:
                sql = f.read()
            sql = sql.format(div_query_path, load_div_query_path)
            empty = get_bq_data(sql, client)
    # get the new min max date
    with open('min_max_date.sql') as f:
        min_max_sql = f.read()
    min_max_sql = min_max_sql.format(price_query_path)
    max_dt2 = get_bq_data(min_max_sql, client)
    new_max_dt = max_dt2['min_max_dt'].iloc[0]
    # check if we're in a new month. if yes, calculate + email returns
    if new_max_dt.month != base_dt.month:
        pct = {}
        for ticker in tickers:
            pct[ticker] = ticker_return(new_max_dt, ticker, price_query_path,
                                        client, div_query_path)
        email = compose_summary_email(pct, name_mapping)
        send_email(email)


def ticker_return(new_max_dt, ticker, query_path, client, div_query_path):
    """Takes in a ticker and calculates the 1 year return
    Args:
        nex_max_dt(datetime): the min max date in the database
        ticker(str): the ticker to pull data from
        query_path(str): the table path to pull stock data from
        client(google big query client): open client to use for querying
        div_query_path(str): the table path to pull dividend data from
    Returns:
        float: the 1 year total return
    """
    # pull start and end dates for the calculation
    end_dt = new_max_dt.replace(day=1)
    start_dt = end_dt.replace(year=end_dt.year-1)
    with open('max_date_where.sql') as f:
        sql_base = f.read()
    sql = sql_base.format(query_path, "'"+end_dt.strftime('%Y-%m-%d')+"'",
                            "'"+ticker+"'")
    end_dt = get_bq_data(sql, client)
    end_dt = end_dt['max_dt'].iloc[0]
    sql = sql_base.format(query_path, "'"+start_dt.strftime('%Y-%m-%d')+"'",
                            "'"+ticker+"'")
    start_dt = get_bq_data(sql, client)
    start_dt = start_dt['max_dt'].iloc[0]
    # get the closing values on the start and end dates
    with open('close_value.sql') as f:
        sql_base = f.read()
    sql = sql_base.format(query_path, "'"+ticker+"'",
                          "'"+end_dt.strftime('%Y-%m-%d')+"'")
    end_close = get_bq_data(sql, client)
    end_close = end_close['close'].iloc[0]
    sql = sql_base.format(query_path, "'"+ticker+"'",
                          "'"+start_dt.strftime('%Y-%m-%d')+"'")
    start_close = get_bq_data(sql, client)
    start_close = start_close['close'].iloc[0]
    # get total dividends paid out during the year
    with open('divs.sql') as f:
        sql_base = f.read()
    sql = sql_base.format(div_query_path, "'"+ticker+"'",
                          "'"+start_dt.strftime('%Y-%m-%d')+"'",
                          "'"+end_dt.strftime('%Y-%m-%d')+"'")
    divs = get_bq_data(sql, client)
    divs = divs['TOT_AMT'].iloc[0]
    # calculate the return
    ticker_return = (end_close / (start_close - divs) - 1) * 100
    return ticker_return


def kickoff(request):
    """Used to kick off main code body inside a try/except structure
    """
    try:
        # try to run the main body of code
        main_kickoff()
    except Exception as e:
        # if it fails. capture the exception and send out a summary email.
        email = error_composition(e)
        send_email(email)


if __name__ == '__main__':
    kickoff('start')s
