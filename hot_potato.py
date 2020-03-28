"""Code used to track 1-year total returns to help enable a hot potato strategy.
"""
import os
import json
import urllib.request as urllib2
import pandas as pd
from mailjet_rest import Client

def get_url(ticker):
    """Takes in a stock ticker and returns the relevant Yahoo Finance link.

    Args:
        ticker(str): the ticker whose info we want

    Returns:
        str: the Yahoo Finance URL of the supplied ticker
    """
    url = 'https://finance.yahoo.com/quote/{arg1}/performance?p={arg1}'.format(arg1=ticker)
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
    json_list = json.loads(tree)
    return json_list['oneYear']['raw']

def send_email(pct, name_mapping):
    """Sends an email whose subject lists the highest performing stock
       and which includes a table showing all stock performance.

    Args:
        pct(dict): maps between stock tickers and 1-year total returns
        name_mapping(dict): maps between stock tickers and their definitions
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
    api_key = os.environ['api_key']
    api_secret = os.environ['api_secret']
    contact_email = os.environ['contact_email']
    contact_name = os.environ['contact_name']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
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
    result = mailjet.send.create(data=data)
    print(result)


def kickoff(request):
    """Function which orchestrates the rest of the code.

    Args:
        request: passed as part of the Google Function orchestration service. Not used.
    """
    # tickers for which we want reports
    tickers = ['VCN.TO', 'VLB.TO', 'VFV.TO', 'VIU.TO']
    # dictionary connecting tickers to readible names. Used in email.
    name_mapping = {'VCN': 'Canada stocks',
                    'VLB': 'Canada Bonds',
                    'VFV': 'S&P 500 Index',
                    'VIU': 'ex-NA stocks'}
    pct = {}
    for ticker in tickers:
        pct[ticker] = get_yearly_return(ticker)
    send_email(pct, name_mapping)
