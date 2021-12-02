"""Code used to track 1-year total returns to help enable a hot potato strategy.
"""
import os
import sys
import traceback
import datetime as dt
import urllib.request as urllib2
import pandas as pd
import yaml
from google.cloud import bigquery
from mailjet_rest import Client
import yfinance as yf
import logging
import email_helpers as eh
import google_helpers as gh


# set logging level
logging.basicConfig(level=logging.INFO)


def get_hist_data(start_dt, ticker):
    start_dt = start_dt.strftime('%Y-%m-%d')
    stock_data = yf.download(ticker, start=start_dt, actions=True)
    stock_data = stock_data.loc[stock_data.index >= start_dt]
    stock_data.reset_index(inplace=True)
    df_price_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df_price = stock_data[df_price_cols].copy()
    df_price.insert(0, 'Ticker', ticker)
    price_float_cols = df_price.columns.drop(['Ticker', 'Date', 'Volume'])
    for col in price_float_cols:
        df_price.loc[:, col] = df_price.loc[:, col].apply(lambda x: round(x, 2))
    df_div_cols = ['Date', 'Dividends']
    df_div = stock_data.loc[stock_data.Dividends > 0, df_div_cols].copy()
    df_div.insert(0, 'Ticker', ticker)
    df_div.loc[:, 'Dividends'] = df_div.loc[:, 'Dividends'].apply(lambda x: round(x, 2))
    return (df_price, df_div)


def compose_summary_email(pct, name_mapping):
    """Composes an email whose subject lists the highest performing stock
       and which includes a table showing all stock performance.

    Args:
        pct (dict): maps between stock tickers and 1-year total returns
        name_mapping (dict): maps between stock tickers and their definitions

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
    subject = "{} has the highest returns".format(highest_return_ticker)
    body = "<h3>Today's leader is {} at {}.</h3><br />Summary:<br />{}".format(highest_return_ticker, highest_return.round(2), summary_table)
    return subject, body


def ticker_return(new_max_dt, ticker, query_path, client, div_query_path):
    """Takes in a ticker and calculates the 1 year return

    Args:
        nex_max_dt (datetime): the min max date in the database
        ticker (str): the ticker to pull data from
        query_path (str): the table path to pull stock data from
        client (google big query client): open client to use for querying
        div_query_path (str): the table path to pull dividend data from

    Returns:
        float: the 1 year total return
    """
    logging.info(ticker)
    end_dt = new_max_dt.replace(day=1)
    start_dt = end_dt.replace(year=end_dt.year-1)
    with open('max_date_where.sql') as sql_file:
        sql_base = sql_file.read()
    sql = sql_base.format(query_path, "'"+end_dt.strftime('%Y-%m-%d')+"'",
                          "'"+ticker+"'")
    end_dt = gh.get_bq_data(sql, client)
    end_dt = end_dt['max_dt'].iloc[0]
    sql = sql_base.format(query_path, "'"+start_dt.strftime('%Y-%m-%d')+"'",
                          "'"+ticker+"'")
    start_dt = gh.get_bq_data(sql, client)
    start_dt = start_dt['max_dt'].iloc[0]
    # get the closing values on the start and end dates
    with open('close_value.sql') as sql_file:
        sql_base = sql_file.read()
    sql = sql_base.format(query_path, "'"+ticker+"'",
                          "'"+end_dt.strftime('%Y-%m-%d')+"'")
    end_close = gh.get_bq_data(sql, client)
    end_close = end_close['close'].iloc[0]
    sql = sql_base.format(query_path, "'"+ticker+"'",
                          "'"+start_dt.strftime('%Y-%m-%d')+"'")
    start_close = gh.get_bq_data(sql, client)
    start_close = start_close['close'].iloc[0]
    # get total dividends paid out during the year
    with open('divs.sql') as sql_file:
        sql_base = sql_file .read()
    sql = sql_base.format(div_query_path, "'"+ticker+"'",
                          "'"+start_dt.strftime('%Y-%m-%d')+"'",
                          "'"+end_dt.strftime('%Y-%m-%d')+"'")
    divs = gh.get_bq_data(sql, client)
    divs = divs['TOT_AMT'].iloc[0]
    # calculate the return
    total_return = (end_close / (start_close - divs) - 1) * 100
    return total_return


def main_kickoff():
    """Function which orchestrates the rest of the code
    """
    with open('stocks.yaml') as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
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
    with open('min_max_date.sql') as sql_file:
        min_max_sql = sql_file.read()
    min_max_sql = min_max_sql.format(price_query_path)
    max_dt = gh.get_bq_data(min_max_sql, client)
    base_dt = max_dt['min_max_dt'].iloc[0]
    # if only have a one date range, return is weird so look at min 7 day range
    pull_dt = base_dt - dt.timedelta(days=7)
    logging.info(pull_dt)
    logging.info(base_dt)
    start_dt = pull_dt.strftime('%Y-%m-%d')

    # empty load tables
    sql = "delete FROM "+load_price_query_path+" where snap_date > '2000-01-01'"
    _ = gh.get_bq_data(sql, client)
    sql = "delete FROM "+load_div_query_path+" where snap_date > '2000-01-01'"
    _ = gh.get_bq_data(sql, client)
    # pull data for each ticker from Yahoo
    for ticker in tickers:
        logging.info('start')
        logging.info(ticker)
        (price_data, div_data) = get_hist_data(pull_dt, ticker)
        # if there is new data, write it to the load tables
        if len(price_data) > 0:
            gh.write_to_gbq(price_data, client, load_price_table)
            with open('merge_price.sql') as sql_file:
                sql = sql_file.read()
            sql = sql.format(price_query_path, load_price_query_path)
            _ = gh.get_bq_data(sql, client)
        if len(div_data) > 0:
            gh.write_to_gbq(div_data, client, load_div_table)
            with open('merge_divs.sql') as sql_file:
                sql = sql_file.read()
            sql = sql.format(div_query_path, load_div_query_path)
            _ = gh.get_bq_data(sql, client)
    # get the new min max date
    with open('min_max_date.sql') as sql_file:
        min_max_sql = sql_file.read()
    min_max_sql = min_max_sql.format(price_query_path)
    max_dt2 = gh.get_bq_data(min_max_sql, client)
    new_max_dt = max_dt2['min_max_dt'].iloc[0]
    logging.info(new_max_dt)
    logging.info('end')

    # check if we're in a new month. if yes, calculate + email returns
    if new_max_dt.month != base_dt.month:
        pct = {}
        for ticker in tickers:
            pct[ticker] = ticker_return(new_max_dt, ticker, price_query_path,
                                        client, div_query_path)
        subject, body = compose_summary_email(pct, name_mapping)
        email = eh.email_composition(os.environ['contact_email'],
                                     os.environ['contact_name'],
                                     subject, body)
        eh.send_email(email)


def error_email_body():
    """Composes the body of the email in the event of an error with a run.
    Returns:
        str: The errors which caused the job to fail.
    """
    err = sys.exc_info()
    err_message = traceback.format_exception(*err)
    err_str = '<br>'.join(err_message)
    err_str = err_str.replace('\n', '')
    body = "There was an errorThere was an error with the hot potatoes run: <br> {}".format(err_str)
    return body


def kickoff(request):
    """Function which orchestrates the rest of the code

    Args:
        request: passed as part of the Google Function orchestration service.
            Not used.
    """
    try:
        # try to run the main body of code
        main_kickoff()
    except Exception:
        # if it fails. capture the exception and send out a summary email.
        subject = "There was an error with the hot potatoes run V3"
        body = error_email_body()
        email = eh.email_composition(os.environ['contact_email'],
                                     os.environ['contact_name'],
                                     subject, body)
        eh.send_email(email)


if __name__ == '__main__':
    kickoff('start')
