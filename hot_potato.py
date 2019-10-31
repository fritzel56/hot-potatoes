import urllib.request as urllib2
import json
from mailjet_rest import Client
import os
import pandas as pd

def get_url(ticker):
    url='https://finance.yahoo.com/quote/{}/performance?p={}'.format(ticker, ticker)
    return url

def get_yearly_return(ticker):
    url = get_url(ticker)
    content = urllib2.urlopen(url).read().decode('utf-8')
    starting = content.find('trailingReturns')+17
    end = content.find("}}", starting)+2
    tree = content[starting:end]
    jsonList = json.loads(tree)
    return jsonList['oneYear']['raw']

def send_email(pct, name_mapping):
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

def kickoff(request):
    tickers = ['VCN.TO', 'VLB.TO', 'VFV.TO', 'VIU.TO']
    name_mapping = {'VCN': 'Canada stocks',
                    'VLB': 'Canada Bonds',
                    'VFV': 'S&P 500 Index',
                    'VIU': 'ex-NA stocks'}
    pct = {}
    for ticker in tickers:
        pct[ticker] = get_yearly_return(ticker)
    send_email(pct, name_mapping)
